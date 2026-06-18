# -*- coding: utf-8 -*-
"""
后台任务路由 — GET /api/tasks, GET /api/tasks/{id}, POST /api/tasks/{id}/cancel
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.task import BackgroundTask
from app.schemas.task import TaskResponse
from app.schemas.common import ApiResponse
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/tasks", tags=["后台任务"])


@router.get("", response_model=ApiResponse)
async def list_tasks(
    task_type: str = None,
    status: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取后台任务列表"""
    tasks = await task_manager.get_tasks(db, task_type=task_type, status=status, limit=limit)
    items = [
        TaskResponse(
            id=t.id,
            task_type=t.task_type,
            status=t.status,
            progress=t.progress,
            message=t.message,
            result_json=t.result_json,
            error=t.error,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tasks
    ]
    return ApiResponse(code=0, data=[item.model_dump() for item in items], message="success")


@router.get("/{task_id}", response_model=ApiResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取单个任务状态"""
    task = await task_manager.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    resp = TaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        message=task.message,
        result_json=task.result_json,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

    return ApiResponse(code=0, data=resp, message="success")


@router.post("/{task_id}/cancel", response_model=ApiResponse)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """取消后台任务"""
    task = await task_manager.cancel_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return ApiResponse(code=0, data={"id": task_id, "status": "cancelled"}, message="任务已取消")
