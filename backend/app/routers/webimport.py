# -*- coding: utf-8 -*-
"""
网页导入路由 — POST /api/webimport/*
"""

import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.webimport import (
    UrlImportRequest,
    BatchUrlImportRequest,
    BilibiliFavoritesRequest,
    BookmarkImportRequest,
    BilibiliFolderItem,
    CookieTestRequest,
    CookieTestResponse,
)
from app.schemas.common import ApiResponse
from app.services.task_manager import task_manager
from app.services.config_manager import config_manager

router = APIRouter(prefix="/api/webimport", tags=["网页导入"])


@router.post("/url", response_model=ApiResponse)
async def import_url(
    request: UrlImportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """导入单个 URL"""
    task = await task_manager.create_task(
        db, task_type="web_import",
        message=f"准备导入: {request.url[:80]}",
    )

    from app.workers.web_import_worker import start_web_import_task
    aio_task = asyncio.create_task(
        start_web_import_task(
            task.id, mode="url", url=request.url,
            provider=request.provider,
        )
    )
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="网页导入任务已创建")


@router.post("/urls", response_model=ApiResponse)
async def import_urls(
    request: BatchUrlImportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """批量导入 URL 列表"""
    task = await task_manager.create_task(
        db, task_type="web_import",
        message=f"准备批量导入 {len(request.urls)} 个链接",
    )

    from app.workers.web_import_worker import start_web_import_task
    aio_task = asyncio.create_task(
        start_web_import_task(
            task.id, mode="urls", urls=request.urls,
            provider=request.provider,
        )
    )
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="批量导入任务已创建")


@router.get("/bilibili/folders", response_model=ApiResponse)
async def get_bilibili_folders(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取 B 站收藏夹列表"""
    from app.services.web_importer import WebImporter

    # 从配置获取 Cookie
    cookie = await config_manager.get_config(db, "BILIBILI_COOKIE") or ""
    if not cookie:
        # 尝试从环境变量获取
        from app.config import settings
        cookie = settings.BILIBILI_COOKIE

    importer = WebImporter(bilibili_cookie=cookie)
    folders = importer.get_bilibili_folders()

    # 检查是否有错误
    if folders and "error" in folders[0]:
        return ApiResponse(code=50101, data=None, message=folders[0]["error"])

    folder_items = [
        BilibiliFolderItem(
            folder_id=f.get("folder_id", 0),
            title=f.get("title", ""),
            media_count=f.get("media_count", 0),
            intro=f.get("intro", ""),
            is_public=f.get("is_public", True),
        )
        for f in folders
    ]

    return ApiResponse(code=0, data=[f.model_dump() for f in folder_items], message="success")


@router.post("/bilibili/favorites", response_model=ApiResponse)
async def import_bilibili_favorites(
    request: BilibiliFavoritesRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """导入 B 站收藏夹"""
    task = await task_manager.create_task(
        db, task_type="web_import",
        message=f"准备导入 B 站收藏夹: {request.folder_id}",
    )

    from app.workers.web_import_worker import start_web_import_task
    aio_task = asyncio.create_task(
        start_web_import_task(
            task.id, mode="bilibili_favorites",
            folder_id=request.folder_id,
            max_videos=request.max_videos,
            provider=request.provider,
        )
    )
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="B站收藏夹导入任务已创建")


@router.post("/bookmarks", response_model=ApiResponse)
async def import_bookmarks(
    request: BookmarkImportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """从书签 HTML 导入"""
    task = await task_manager.create_task(
        db, task_type="web_import",
        message=f"准备从书签导入: {request.bookmark_path}",
    )

    from app.workers.web_import_worker import start_web_import_task
    aio_task = asyncio.create_task(
        start_web_import_task(
            task.id, mode="bookmarks",
            bookmark_path=request.bookmark_path,
            max_links=request.max_links,
            provider=request.provider,
        )
    )
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="书签导入任务已创建")


@router.post("/bilibili/test-cookie", response_model=ApiResponse)
async def test_bilibili_cookie(
    request: CookieTestRequest,
) -> dict:
    """测试 B 站 Cookie"""
    from app.services.web_importer import BilibiliFetcher

    fetcher = BilibiliFetcher(cookie_str=request.cookie)
    ok, msg = fetcher.test_auth()

    return ApiResponse(
        code=0 if ok else 50101,
        data=CookieTestResponse(success=ok, message=msg).model_dump(),
        message=msg,
    )


@router.post("/xiaohongshu/test-cookie", response_model=ApiResponse)
async def test_xiaohongshu_cookie(
    request: CookieTestRequest,
) -> dict:
    """测试小红书 Cookie"""
    from app.services.web_importer import XiaohongshuFetcher

    fetcher = XiaohongshuFetcher(cookie_str=request.cookie)
    # 小红书没有直接验证接口，尝试访问一个笔记
    return ApiResponse(
        code=0,
        data=CookieTestResponse(success=True, message="Cookie 已设置，具体效果需在实际导入时验证").model_dump(),
        message="Cookie 已设置",
    )
