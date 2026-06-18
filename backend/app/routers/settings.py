# -*- coding: utf-8 -*-
"""
系统配置路由 — GET /api/settings, PUT /api/settings, GET /api/dashboard/stats
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.document import Document
from app.models.profile import KnowledgeProfile
from app.models.task import BackgroundTask
from app.schemas.settings import ConfigItem, ConfigUpdateRequest, ConfigResponse, DashboardStats
from app.schemas.common import ApiResponse
from app.services.config_manager import config_manager
from app.services.search_engine import search_engine

router = APIRouter(prefix="/api", tags=["系统配置"])


@router.get("/settings", response_model=ApiResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取全部配置"""
    configs = await config_manager.get_all_configs(db)
    items = [
        ConfigItem(
            key=c["key"],
            value=c["value"] if not c["is_sensitive"] else "******",
            value_type=c["value_type"],
            description=c["description"],
            is_sensitive=c["is_sensitive"],
        )
        for c in configs
    ]
    return ApiResponse(code=0, data=ConfigResponse(configs=items), message="success")


@router.put("/settings", response_model=ApiResponse)
async def update_settings(
    request: ConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新配置"""
    updated = await config_manager.update_configs(db, [c.model_dump() for c in request.configs])
    return ApiResponse(code=0, data={"updated_count": updated}, message=f"已更新 {updated} 项配置")


@router.get("/dashboard/stats", response_model=ApiResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取仪表盘统计数据"""
    # 文档统计
    total_docs = (await db.execute(select(func.count()).select_from(Document))).scalar() or 0
    category_dist = dict(
        (await db.execute(
            select(Document.category, func.count()).group_by(Document.category)
        )).all()
    )
    type_dist = dict(
        (await db.execute(
            select(Document.doc_type, func.count()).group_by(Document.doc_type)
        )).all()
    )

    # 章节统计
    from app.models.document import Section
    total_sections = (await db.execute(select(func.count()).select_from(Section))).scalar() or 0

    # 标签统计
    from app.models.document import Tag
    total_tags = (await db.execute(select(func.count()).select_from(Tag))).scalar() or 0

    # 最近文档
    recent_stmt = select(Document).order_by(Document.created_at.desc()).limit(5)
    recent_docs = (await db.execute(recent_stmt)).scalars().all()
    recent_list = [
        {"id": d.id, "title": d.title, "category": d.category, "created_at": d.created_at.isoformat()}
        for d in recent_docs
    ]

    # 画像状态
    has_profile = (await db.execute(
        select(func.count()).select_from(KnowledgeProfile)
    )).scalar() > 0

    stats = DashboardStats(
        total_documents=total_docs,
        total_sections=total_sections,
        total_tags=total_tags,
        category_distribution=category_dist,
        type_distribution=type_dist,
        recent_documents=recent_list,
        index_ready=search_engine.is_ready,
        has_profile=has_profile,
    )

    return ApiResponse(code=0, data=stats, message="success")
