# -*- coding: utf-8 -*-
"""
知识画像路由 — GET /api/profile, POST /api/profile/refresh, GET /api/profile/status
"""

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.profile import KnowledgeProfile
from app.schemas.profile import ProfileResponse, ProfileStatusResponse
from app.schemas.common import ApiResponse
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/profile", tags=["知识画像"])


@router.get("", response_model=ApiResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取知识画像（返回最新一条）"""
    stmt = select(KnowledgeProfile).order_by(KnowledgeProfile.created_at.desc()).limit(1)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        return ApiResponse(code=0, data=None, message="暂无画像数据，请先生成画像")

    # 解析 profile_json
    profile_data = profile.profile_json or {}

    resp = ProfileResponse(
        id=profile.id,
        generated_by=profile.generated_by,
        total_documents=profile.total_documents,
        knowledge_units=profile.knowledge_units,
        main_focus=profile.main_focus,
        profile_json=profile_data,
        overview=profile_data.get("overview"),
        theme_distribution=profile_data.get("theme_distribution"),
        tag_ranking=profile_data.get("tag_ranking"),
        knowledge_clusters=profile_data.get("knowledge_clusters"),
        learning_timeline=profile_data.get("learning_timeline"),
        knowledge_gaps=profile_data.get("knowledge_gaps"),
        learning_path=profile_data.get("learning_path"),
        growth_suggestions=profile_data.get("growth_suggestions"),
        llm_profile=profile_data.get("llm_profile"),
        created_at=profile.created_at,
    )

    return ApiResponse(code=0, data=resp, message="success")


@router.post("/refresh", response_model=ApiResponse)
async def refresh_profile(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """手动刷新画像"""
    task = await task_manager.create_task(
        db, task_type="profile_generate",
        message="准备生成知识画像",
    )

    from app.workers.profile_worker import start_profile_task
    aio_task = asyncio.create_task(start_profile_task(task.id))
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="画像生成任务已创建")


@router.get("/status", response_model=ApiResponse)
async def get_profile_status(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取画像生成状态"""
    # 检查是否有正在运行的画像任务
    from app.models.task import BackgroundTask
    stmt = select(BackgroundTask).where(
        BackgroundTask.task_type == "profile_generate",
        BackgroundTask.status.in_(["pending", "running"]),
    )
    result = await db.execute(stmt)
    running_task = result.scalar_one_or_none()

    # 检查是否有画像数据
    profile_stmt = select(KnowledgeProfile).order_by(KnowledgeProfile.created_at.desc()).limit(1)
    profile_result = await db.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()

    status = ProfileStatusResponse(
        is_generating=running_task is not None,
        has_profile=profile is not None,
        last_generated_at=profile.created_at.isoformat() if profile else None,
    )

    return ApiResponse(code=0, data=status, message="success")
