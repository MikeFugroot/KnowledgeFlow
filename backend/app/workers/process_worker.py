# -*- coding: utf-8 -*-
"""
文件处理 Worker — 文件解析 + LLM 整理 + 入库

重要：由于 SQLAlchemy + aiosqlite 在 asyncio.create_task 中存在 greenlet 上下文丢失问题，
后台任务改用同步引擎 (SyncSessionLocal) + asyncio.to_thread 运行。
LLM 调用仍使用 httpx 异步客户端，通过 async_helper 在同步上下文中桥接。
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select

from app.database import SyncSessionLocal
from app.models.document import Document, Section, Tag, document_tag_table
from app.models.raw_doc import RawDocument
from app.models.task import BackgroundTask
from app.services.file_parser import read_any_file
from app.services.llm_organizer import organize_doc
from app.services.task_manager import task_manager
from app.utils.text import clean_text

logger = logging.getLogger(__name__)


def _update_task_sync(db, task_id: int, **kwargs) -> None:
    """同步更新后台任务状态（直接操作 ORM，不走 task_manager 的 async 方法）"""
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


def _process_docs_sync(task_id: int, document_ids: List[int], provider: Optional[str] = None) -> None:
    """
    同步执行文件处理（在独立线程中运行，避免 aiosqlite greenlet 问题）
    """
    with SyncSessionLocal() as db:
        try:
            _update_task_sync(db, task_id, status="running", progress=0.0, message="开始处理文件")

            # 查询文档
            stmt = select(Document).where(Document.id.in_(document_ids))
            docs = db.execute(stmt).scalars().all()

            total = len(docs)
            if total == 0:
                _update_task_sync(db, task_id, status="completed", progress=1.0, message="无文件需要处理")
                return

            processed = 0
            for idx, doc in enumerate(docs, start=1):
                try:
                    _update_task_sync(
                        db, task_id,
                        progress=(idx - 1) / total,
                        message=f"正在处理：{doc.original_title}",
                    )

                    # 1. 文件解析（同步）
                    path = Path(doc.source_path) if doc.source_path else None
                    if path and path.exists():
                        parsed = read_any_file(path)
                    else:
                        parsed = {
                            "type": doc.doc_type,
                            "path": doc.source_path,
                            "url": doc.source_url,
                            "success": True,
                            "title": doc.original_title,
                            "text": "",
                            "error": "",
                        }

                    if not parsed.get("success"):
                        logger.warning(f"解析失败：{parsed.get('error')}")
                        processed += 1
                        continue

                    # 保存原始解析结果
                    raw_doc = RawDocument(
                        document_id=doc.id,
                        doc_type=parsed.get("type", "unknown"),
                        raw_text=parsed.get("text", ""),
                        pages_json=parsed.get("pages"),
                        segments_json=parsed.get("segments"),
                    )
                    db.add(raw_doc)

                    # 2. LLM 整理（需要在事件循环中运行异步代码）
                    if not clean_text(parsed.get("text", "")):
                        from app.services.llm_organizer import can_use_qwen_doc_turbo
                        if not can_use_qwen_doc_turbo(parsed):
                            logger.warning("无有效文本，跳过 LLM 整理")
                            processed += 1
                            continue

                    # 从同步线程中调用异步 LLM 方法
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        # 已有事件循环在运行（我们就是从 asyncio.create_task 进来的）
                        organized = asyncio.run_coroutine_threadsafe(
                            _organize_doc_async(parsed, provider=provider),
                            loop,
                        ).result(timeout=300)
                    else:
                        # 没有事件循环，直接创建
                        organized = asyncio.run(
                            _organize_doc_async(parsed, provider=provider)
                        )

                    # 3. 更新文档记录
                    doc.title = organized.get("title_suggestion") or doc.original_title
                    doc.category = organized.get("category", "其他")
                    doc.summary = organized.get("summary", "")
                    doc.overall_evaluation = organized.get("overall_evaluation", "")
                    doc.title_suggestion = organized.get("title_suggestion", "")
                    doc.reason = organized.get("reason", "")
                    doc.search_text = organized.get("search_text", "")
                    doc.method = organized.get("method", "")
                    doc.model = organized.get("model", "")
                    doc.ai_file_reading = organized.get("method") == "qwen_doc_file"
                    doc.char_count = len(parsed.get("text", ""))

                    # 4. 保存章节
                    for sec_data in organized.get("sections", []):
                        section = Section(
                            document_id=doc.id,
                            section_title=sec_data.get("section_title", ""),
                            location_hint=sec_data.get("location_hint", ""),
                            summary=sec_data.get("summary", ""),
                            search_text=sec_data.get("search_text", ""),
                        )
                        db.add(section)

                    # 5. 保存标签
                    for tag_name in organized.get("tags", []):
                        tag_stmt = select(Tag).where(Tag.name == tag_name)
                        tag = db.execute(tag_stmt).scalar_one_or_none()
                        if tag is None:
                            tag = Tag(name=tag_name)
                            db.add(tag)
                            db.flush()
                        # 添加关联
                        db.execute(
                            document_tag_table.insert().values(document_id=doc.id, tag_id=tag.id)
                        )

                    db.commit()
                    processed += 1

                    logger.info(
                        f"完成：{organized.get('category')} | {'、'.join(organized.get('tags', []))} | {organized.get('method')}"
                    )

                except Exception as e:
                    logger.error(f"处理文档 {doc.id} 失败: {e}", exc_info=True)
                    processed += 1
                    continue

            _update_task_sync(
                db, task_id,
                status="completed",
                progress=1.0,
                message=f"处理完成：成功 {processed}/{total}",
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"文件处理任务失败: {e}\n{tb}")
            _update_task_sync(
                db, task_id,
                status="failed",
                error=tb[-2000:],
                message=f"任务失败: {str(e)}",
            )


async def start_process_task(
    task_id: int,
    document_ids: List[int],
    provider: Optional[str] = None,
) -> None:
    """
    启动文件处理任务

    使用 asyncio.to_thread 在独立线程中运行同步代码，
    避免 aiosqlite 在 asyncio.create_task 中的 greenlet 上下文丢失问题。
    """
    loop = asyncio.get_running_loop()
    await asyncio.to_thread(
        _process_docs_sync, task_id, document_ids, provider
    )
