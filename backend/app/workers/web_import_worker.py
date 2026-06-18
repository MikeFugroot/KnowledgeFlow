# -*- coding: utf-8 -*-
"""
网页导入 Worker — 抓取 + 整理 + 入库

重要：由于 SQLAlchemy + aiosqlite 在 asyncio.create_task 中存在 greenlet 上下文丢失问题，
后台任务改用同步引擎 (SyncSessionLocal) + asyncio.to_thread 运行。
LLM 调用仍使用 httpx 异步客户端，通过 asyncio.run_coroutine_threadsafe 桥接。
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from app.database import SyncSessionLocal
from app.models.document import Document, Section, Tag, document_tag_table
from app.models.task import BackgroundTask
from app.services.web_importer import WebImporter, web_doc_to_pipeline_doc
from app.services.llm_organizer import organize_doc
from app.services.task_manager import task_manager
from app.services.config_manager import config_manager
from app.utils.text import clean_text
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


async def _organize_doc_async(parsed: dict, provider: Optional[str] = None, log_func=None) -> dict:
    """异步调用 LLM 整理（桥接方法）"""
    return await organize_doc(parsed, provider=provider, log_func=log_func)


def _web_import_sync(
    task_id: int,
    mode: str,
    url: str = "",
    urls: Optional[List[str]] = None,
    folder_id: int = 0,
    max_videos: int = 20,
    bookmark_path: str = "",
    max_links: int = 50,
    provider: Optional[str] = None,
) -> None:
    """
    同步执行网页导入（在独立线程中运行，避免 aiosqlite greenlet 问题）
    """
    with SyncSessionLocal() as db:
        try:
            _update_task_sync(db, task_id, status="running", progress=0.0, message="开始网页导入")

            # 获取配置（使用同步查询，带解密）
            from app.models.system_config import SystemConfig
            from app.utils.crypto import decrypt_value, is_encrypted

            bili_cookie = settings.BILIBILI_COOKIE
            xhs_cookie = settings.XHS_COOKIE

            config_stmt = select(SystemConfig)
            config_result = db.execute(config_stmt)
            for cfg in config_result.scalars().all():
                val = decrypt_value(cfg.value_encrypted) if is_encrypted(cfg.value_encrypted) else cfg.value_encrypted
                if cfg.key == "BILIBILI_COOKIE" and val:
                    bili_cookie = val
                elif cfg.key == "XHS_COOKIE" and val:
                    xhs_cookie = val

            whisper_size = settings.whisper_model_candidates_list[0] if settings.whisper_model_candidates_list else "medium"

            importer = WebImporter(
                bilibili_cookie=bili_cookie,
                xiaohongshu_cookie=xhs_cookie,
                whisper_fallback=True,
                whisper_model_size=whisper_size,
                progress_callback=lambda msg: None,
            )

            # 抓取网页内容（同步操作）
            web_docs = []
            if mode == "url":
                web_docs = [importer.import_from_url(url)]
            elif mode == "urls":
                web_docs = importer.import_from_urls(urls or [])
            elif mode == "bilibili_favorites":
                web_docs = importer.import_bilibili_favorites(folder_id=folder_id, max_videos=max_videos)
            elif mode == "bookmarks":
                web_docs = importer.import_from_bookmarks(bookmark_path, max_links=max_links)
            else:
                _update_task_sync(db, task_id, status="failed", error=f"未知导入模式: {mode}")
                return

            if not web_docs:
                _update_task_sync(db, task_id, status="completed", progress=1.0, message="没有抓取到任何内容")
                return

            total = len(web_docs)

            processed = 0
            for idx, web_doc in enumerate(web_docs, start=1):
                try:
                    _update_task_sync(
                        db, task_id,
                        progress=(idx - 1) / total,
                        message=f"正在整理：{web_doc.get('title', '')[:40]}",
                    )

                    # 转为管道格式
                    doc = web_doc_to_pipeline_doc(web_doc)
                    if not doc.get("success"):
                        continue

                    # LLM 整理（桥接到异步）
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        organized = asyncio.run_coroutine_threadsafe(
                            _organize_doc_async(doc, provider=provider),
                            loop,
                        ).result(timeout=300)
                    else:
                        organized = asyncio.run(
                            _organize_doc_async(doc, provider=provider)
                        )

                    # 创建文档记录
                    source_type = web_doc.get("source_type", "webpage")
                    source_url = web_doc.get("source_url", "")
                    title = organized.get("title_suggestion") or doc.get("title", "untitled")

                    new_doc = Document(
                        title=title,
                        original_title=web_doc.get("title", ""),
                        doc_type=source_type,
                        source_path="",
                        source_url=source_url,
                        char_count=len(doc.get("text", "")),
                        ai_file_reading=organized.get("method") == "qwen_doc_file",
                        method=organized.get("method", ""),
                        model=organized.get("model", ""),
                        category=organized.get("category", "其他"),
                        summary=organized.get("summary", ""),
                        overall_evaluation=organized.get("overall_evaluation", ""),
                        title_suggestion=organized.get("title_suggestion", ""),
                        reason=organized.get("reason", ""),
                        search_text=organized.get("search_text", ""),
                    )
                    db.add(new_doc)
                    db.flush()

                    # 保存章节
                    for sec_data in organized.get("sections", []):
                        section = Section(
                            document_id=new_doc.id,
                            section_title=sec_data.get("section_title", ""),
                            location_hint=sec_data.get("location_hint", ""),
                            summary=sec_data.get("summary", ""),
                            search_text=sec_data.get("search_text", ""),
                        )
                        db.add(section)

                    # 保存标签
                    for tag_name in organized.get("tags", []):
                        tag_stmt = select(Tag).where(Tag.name == tag_name)
                        tag = db.execute(tag_stmt).scalar_one_or_none()
                        if tag is None:
                            tag = Tag(name=tag_name)
                            db.add(tag)
                            db.flush()
                        db.execute(
                            document_tag_table.insert().values(document_id=new_doc.id, tag_id=tag.id)
                        )

                    db.commit()
                    processed += 1

                except Exception as e:
                    logger.error(f"整理网页内容失败: {e}", exc_info=True)
                    continue

            _update_task_sync(
                db, task_id,
                status="completed",
                progress=1.0,
                message=f"网页导入完成：成功整理 {processed}/{total} 条",
            )

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"网页导入任务失败: {e}\n{tb}")
            _update_task_sync(
                db, task_id,
                status="failed",
                error=tb[-2000:],
                message=f"任务失败: {str(e)}",
            )


async def start_web_import_task(
    task_id: int,
    mode: str,
    url: str = "",
    urls: Optional[List[str]] = None,
    folder_id: int = 0,
    max_videos: int = 20,
    bookmark_path: str = "",
    max_links: int = 50,
    provider: Optional[str] = None,
) -> None:
    """
    启动网页导入任务

    使用 asyncio.to_thread 在独立线程中运行同步代码，
    避免 aiosqlite 在 asyncio.create_task 中的 greenlet 上下文丢失问题。
    """
    await asyncio.to_thread(
        _web_import_sync,
        task_id, mode, url, urls, folder_id, max_videos,
        bookmark_path, max_links, provider,
    )
