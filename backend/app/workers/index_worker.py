# -*- coding: utf-8 -*-
"""
索引构建 Worker — 构建语义检索向量索引

重要：由于 SQLAlchemy + aiosqlite 在 asyncio.create_task 中存在 greenlet 上下文丢失问题，
后台任务改用同步引擎 (SyncSessionLocal) + asyncio.to_thread 运行。
索引构建的核心计算（embedding + FAISS）是同步操作，不再依赖异步数据库会话。
"""

import asyncio
import logging
from datetime import datetime

from app.database import SyncSessionLocal
from app.services.search_engine import search_engine
from app.services.task_manager import task_manager
from app.routers.ws import ws_manager
from app.models.task import BackgroundTask

logger = logging.getLogger(__name__)


def _update_task_sync(db, task_id: int, **kwargs) -> None:
    """同步更新后台任务状态"""
    task = db.get(BackgroundTask, task_id)
    if task is None:
        return
    for key, value in kwargs.items():
        if value is not None:
            setattr(task, key, value)
    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)


async def _broadcast_ws(event_type: str, data: dict) -> None:
    """异步 WebSocket 广播（桥接方法）"""
    await ws_manager.broadcast(event_type, data)


def _build_index_sync(task_id: int) -> None:
    """
    同步执行索引构建（在独立线程中运行，避免 aiosqlite greenlet 问题）

    使用 search_engine 的同步构建方法，通过 SyncSessionLocal 加载数据。
    """
    try:
        with SyncSessionLocal() as db:
            _update_task_sync(db, task_id, status="running", progress=0.0, message="开始构建检索索引")

        # 调用同步版索引构建
        def log_fn(msg: str) -> None:
            logger.info(f"[索引构建] {msg}")

        search_engine.build_index_sync(log_func=log_fn)

        # 广播索引状态
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(
                    _broadcast_ws("index_status", {
                        "is_ready": True,
                        "total_chunks": search_engine.total_chunks,
                    })
                )
            )
        except RuntimeError:
            pass

        with SyncSessionLocal() as db:
            _update_task_sync(
                db, task_id,
                status="completed",
                progress=1.0,
                message=f"索引构建完成：{search_engine.total_chunks} 个文本块",
            )

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"索引构建任务失败: {e}\n{tb}")

        # 广播失败状态
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(
                    _broadcast_ws("index_status", {
                        "is_ready": False,
                        "error": str(e),
                    })
                )
            )
        except RuntimeError:
            pass

        with SyncSessionLocal() as db:
            _update_task_sync(
                db, task_id,
                status="failed",
                error=tb[-2000:],
                message=f"索引构建失败: {str(e)}",
            )


async def start_index_build_task(task_id: int) -> None:
    """
    启动索引构建任务

    使用 asyncio.to_thread 在独立线程中运行同步代码，
    避免 aiosqlite 在 asyncio.create_task 中的 greenlet 上下文丢失问题。
    """
    await asyncio.to_thread(_build_index_sync, task_id)
