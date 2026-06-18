# -*- coding: utf-8 -*-
"""
后台任务管理器 — 任务调度 + 状态追踪 + WebSocket 进度推送
使用 asyncio 替代 QThread，ARQ 用于异步任务队列
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import BackgroundTask
from app.schemas.task import TaskProgressPayload

logger = logging.getLogger(__name__)


class TaskManager:
    """后台任务管理器"""

    def __init__(self) -> None:
        self._running_tasks: Dict[int, asyncio.Task] = {}
        self._ws_manager: Optional[Any] = None  # WebSocket 管理器引用

    def set_ws_manager(self, ws_manager: Any) -> None:
        """设置 WebSocket 管理器引用"""
        self._ws_manager = ws_manager

    async def create_task(
        self,
        db: AsyncSession,
        task_type: str,
        message: str = "任务已创建",
    ) -> BackgroundTask:
        """创建新的后台任务记录"""
        task = BackgroundTask(
            task_type=task_type,
            status="pending",
            progress=0.0,
            message=message,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def update_task(
        self,
        db: AsyncSession,
        task_id: int,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        result_json: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[BackgroundTask]:
        """更新后台任务状态"""
        task = await db.get(BackgroundTask, task_id)
        if task is None:
            return None

        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if result_json is not None:
            task.result_json = result_json
        if error is not None:
            task.error = error
        task.updated_at = datetime.now()

        await db.commit()
        await db.refresh(task)

        # 通过 WebSocket 推送进度
        await self._broadcast_progress(task)

        return task

    async def get_task(self, db: AsyncSession, task_id: int) -> Optional[BackgroundTask]:
        """获取单个任务"""
        return await db.get(BackgroundTask, task_id)

    async def get_tasks(
        self,
        db: AsyncSession,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[BackgroundTask]:
        """获取任务列表"""
        stmt = select(BackgroundTask).order_by(BackgroundTask.created_at.desc())
        if task_type:
            stmt = stmt.where(BackgroundTask.task_type == task_type)
        if status:
            stmt = stmt.where(BackgroundTask.status == status)
        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def cancel_task(self, db: AsyncSession, task_id: int) -> Optional[BackgroundTask]:
        """取消后台任务"""
        task = await db.get(BackgroundTask, task_id)
        if task is None:
            return None
        if task.status not in ("pending", "running"):
            return task

        # 取消 asyncio 任务
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]

        task.status = "cancelled"
        task.message = "任务已取消"
        task.updated_at = datetime.now()
        await db.commit()
        await db.refresh(task)

        await self._broadcast_progress(task)
        return task

    def register_asyncio_task(self, task_id: int, aio_task: asyncio.Task) -> None:
        """注册 asyncio 任务，用于后续取消"""
        self._running_tasks[task_id] = aio_task

    def unregister_asyncio_task(self, task_id: int) -> None:
        """注销 asyncio 任务"""
        self._running_tasks.pop(task_id, None)

    async def _broadcast_progress(self, task: BackgroundTask) -> None:
        """通过 WebSocket 广播任务进度"""
        if self._ws_manager is None:
            return

        # 确定消息类型
        msg_type = "task_progress"
        if task.status == "completed":
            msg_type = "task_completed"
        elif task.status == "failed":
            msg_type = "task_failed"

        payload = TaskProgressPayload(
            task_id=task.id,
            task_type=task.task_type,
            current=int(task.progress * 100),
            total=100,
            message=task.message,
        )

        await self._ws_manager.broadcast(
            msg_type=msg_type,
            payload=payload.model_dump(),
        )

    async def broadcast_log(self, level: str, message: str) -> None:
        """通过 WebSocket 广播日志"""
        if self._ws_manager is None:
            return
        await self._ws_manager.broadcast(
            msg_type="log",
            payload={"level": level, "message": message},
        )


# 全局任务管理器实例
task_manager = TaskManager()
