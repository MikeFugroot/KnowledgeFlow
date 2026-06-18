# -*- coding: utf-8 -*-
"""
语义检索路由。
"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.document import Document
from app.schemas.search import SearchRequest, SearchResponse, SearchHit, IndexStatusResponse
from app.schemas.common import ApiResponse
from app.services.search_engine import search_engine
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/search", tags=["语义检索"])


def _source_keys(source: str) -> set[str]:
    if not source:
        return set()
    raw = str(source).strip()
    keys = {raw, raw.replace("\\", "/")}
    try:
        keys.add(str(Path(raw).resolve()).replace("\\", "/"))
    except Exception:
        pass
    return {key for key in keys if key}


async def _resolve_document_ids(results: list[dict], db: AsyncSession) -> dict[str, int]:
    if not any(not r.get("document_id") and r.get("source") for r in results):
        return {}

    source_to_document_id: dict[str, int] = {}
    doc_result = await db.execute(select(Document.id, Document.source_path, Document.source_url))
    for doc_id, source_path, source_url in doc_result.all():
        for source in (source_path, source_url):
            if not source:
                continue
            for key in _source_keys(str(source)):
                source_to_document_id[key] = doc_id
    return source_to_document_id


def _lookup_document_id(source_to_document_id: dict[str, int], source: str) -> int | None:
    for key in _source_keys(source):
        if key in source_to_document_id:
            return source_to_document_id[key]
    return None


@router.post("", response_model=ApiResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """执行语义检索。"""
    if not search_engine.is_ready:
        raise HTTPException(status_code=400, detail="检索索引未就绪，请先构建索引")

    try:
        search_engine.ensure_model_loaded()
        results = await search_engine.search(request.query, top_k=request.top_k)
        source_to_document_id = await _resolve_document_ids(results, db)

        hits = [
            SearchHit(
                rank=r.get("rank", 0),
                doc_title=r.get("doc_title", ""),
                doc_type=r.get("doc_type", ""),
                source=r.get("source", ""),
                location=r.get("location", ""),
                section_title=r.get("section_title", ""),
                chunk_text=r.get("chunk_text", "")[:500],
                score=r.get("score", 0.0),
                dense_score=r.get("dense_score", 0.0),
                lexical_score=r.get("lexical_score", 0.0),
                match_reason=r.get("match_reason", ""),
                hit_terms=r.get("hit_terms", []),
                document_id=r.get("document_id") or _lookup_document_id(source_to_document_id, str(r.get("source") or "")),
            )
            for r in results
        ]

        return ApiResponse(
            code=0,
            data=SearchResponse(
                query=request.query,
                total=len(hits),
                results=hits,
            ),
            message="success",
        )
    except Exception as e:
        return ApiResponse(code=50001, data=None, message=f"检索失败: {str(e)}")


@router.post("/index/build", response_model=ApiResponse)
async def build_index(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """触发索引构建。"""
    task = await task_manager.create_task(
        db,
        task_type="index_build",
        message="准备构建检索索引",
    )

    from app.workers.index_worker import start_index_build_task

    aio_task = asyncio.create_task(start_index_build_task(task.id))
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="索引构建任务已创建")


@router.get("/index/status", response_model=ApiResponse)
async def get_index_status(db: AsyncSession = Depends(get_db)) -> dict:
    """获取索引状态。"""
    total_documents = (await db.execute(select(func.count()).select_from(Document))).scalar() or 0
    status = IndexStatusResponse(
        is_ready=search_engine.is_ready,
        total_chunks=search_engine.total_chunks,
        total_documents=total_documents,
        last_built_at=search_engine.last_built_at,
        embedding_model=search_engine._embedding_model_name,
    )

    return ApiResponse(code=0, data=status, message="success")
