# -*- coding: utf-8 -*-
"""
知识画像生成 Worker — 规则画像 + 可选 LLM 深度画像

重要：由于 SQLAlchemy + aiosqlite 在 asyncio.create_task 中存在 greenlet 上下文丢失问题，
后台任务改用同步引擎 (SyncSessionLocal) + asyncio.to_thread 运行。
LLM 调用仍使用 httpx 异步客户端，通过 async_helper 在同步上下文中桥接。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import SyncSessionLocal
from app.models.document import Document
from app.models.profile import KnowledgeProfile
from app.models.task import BackgroundTask
from app.services.profile_builder import (
    build_rule_based_knowledge_profile,
    call_llm_profile_api,
)
from app.services.task_manager import task_manager
from app.routers.ws import ws_manager
from app.config import settings

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


async def _call_llm_profile_async(items, base_profile, log_func=None):
    """异步调用 LLM 画像生成（桥接方法）"""
    return await call_llm_profile_api(items, base_profile, log_func=log_func)


async def _broadcast_ws(event_type: str, data: dict) -> None:
    """异步 WebSocket 广播（桥接方法）"""
    await ws_manager.broadcast(event_type, data)


def _generate_profile_sync(task_id: int, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """
    同步执行画像生成（在独立线程中运行，避免 aiosqlite greenlet 问题）

    Args:
        task_id: 后台任务 ID
        loop: 外部事件循环引用，用于 WebSocket 广播和 LLM 异步调用桥接
    """
    # 辅助函数：安全广播 WebSocket（通过外部事件循环桥接）
    def _ws_broadcast(event_type: str, data: dict) -> None:
        if loop and loop.is_running():
            loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(_broadcast_ws(event_type, data))
            )

    with SyncSessionLocal() as db:
        try:
            _update_task_sync(db, task_id, status="running", progress=0.0, message="开始生成知识画像")

            # 1. 加载所有文档
            stmt = select(Document).options(selectinload(Document.sections), selectinload(Document.tags))
            result = db.execute(stmt)
            docs = result.scalars().all()

            if not docs:
                _update_task_sync(db, task_id, status="completed", progress=1.0, message="暂无文档，无法生成画像")
                _ws_broadcast("profile_status", {"status": "completed", "total_documents": 0})
                return

            # 2. 构建文档列表（与桌面版格式兼容）
            items = []
            for doc in docs:
                item = {
                    "document": {
                        "type": doc.doc_type,
                        "title": doc.original_title,
                        "path": doc.source_path,
                        "url": doc.source_url,
                        "char_count": doc.char_count,
                    },
                    "organized": {
                        "category": doc.category,
                        "tags": [t.name for t in doc.tags],
                        "summary": doc.summary,
                        "overall_evaluation": doc.overall_evaluation,
                        "title_suggestion": doc.title_suggestion,
                        "reason": doc.reason,
                        "method": doc.method,
                        "model": doc.model,
                        "search_text": doc.search_text,
                        "sections": [
                            {
                                "section_title": s.section_title,
                                "location_hint": s.location_hint,
                                "summary": s.summary,
                                "search_text": s.search_text,
                            }
                            for s in doc.sections
                        ],
                    },
                }
                items.append(item)

            _update_task_sync(db, task_id, progress=0.3, message="规则画像生成中...")

            # 3. 生成规则画像（同步计算）
            base_profile = build_rule_based_knowledge_profile(items)

            # 广播规则画像完成
            _ws_broadcast("profile_status", {
                "status": "rule_based_done",
                "total_documents": len(items),
            })

            _update_task_sync(db, task_id, progress=0.6, message="规则画像已完成")

            # 4. 可选：LLM 深度画像
            profile = base_profile
            if settings.USE_LLM_PROFILE_GENERATION:
                try:
                    _update_task_sync(db, task_id, progress=0.7, message="LLM 深度画像生成中...")

                    async def profile_log(msg: str) -> None:
                        await task_manager.broadcast_log("INFO", msg)

                    # 从同步线程中调用异步 LLM 方法（通过桥接）
                    if loop and loop.is_running():
                        profile = asyncio.run_coroutine_threadsafe(
                            _call_llm_profile_async(items, base_profile, log_func=profile_log),
                            loop,
                        ).result(timeout=300)
                    else:
                        # 无外部事件循环时回退到 asyncio.run
                        profile = asyncio.run(
                            _call_llm_profile_async(items, base_profile, log_func=profile_log)
                        )

                    _ws_broadcast("profile_status", {
                        "status": "llm_done",
                        "total_documents": len(items),
                    })

                except Exception as e:
                    logger.warning(f"LLM 画像生成失败，使用规则画像兜底: {e}")

            # 5. 保存画像到数据库
            overview = profile.get("overview", {})
            kp = KnowledgeProfile(
                generated_by=profile.get("generated_by", "rule_based"),
                profile_json=profile,
                total_documents=overview.get("total_documents", len(items)),
                knowledge_units=overview.get("knowledge_units", 0),
                main_focus=overview.get("main_focus", ""),
            )
            db.add(kp)
            db.commit()

            # 广播画像完成
            _ws_broadcast("profile_status", {
                "status": "completed",
                "total_documents": len(items),
            })

            _update_task_sync(
                db, task_id,
                status="completed",
                progress=1.0,
                message=f"知识画像生成完成：{len(items)} 篇文档",
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"知识画像任务失败: {e}\n{tb}")
            _update_task_sync(
                db, task_id,
                status="failed",
                error=tb[-2000:],
                message=f"画像生成失败: {str(e)}",
            )
            # 通知前端任务失败
            _ws_broadcast("profile_status", {
                "status": "failed",
                "error": str(e),
            })


async def start_profile_task(task_id: int) -> None:
    """
    启动知识画像生成任务

    使用 asyncio.to_thread 在独立线程中运行同步代码，
    避免 aiosqlite 在 asyncio.create_task 中的 greenlet 上下文丢失问题。
    同时传递事件循环引用，确保 WebSocket 广播和 LLM 异步调用可以桥接。
    """
    loop = asyncio.get_running_loop()
    await asyncio.to_thread(_generate_profile_sync, task_id, loop)
