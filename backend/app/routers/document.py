# -*- coding: utf-8 -*-
"""
文档管理路由 — GET/PUT/DELETE /api/documents/*
"""

import re
import os
import subprocess
import sys
import platform
import time
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db
from app.models.document import Document, Section, Tag, document_tag_table
from app.schemas.document import (
    DocumentResponse,
    DocumentListItem,
    DocumentUpdate,
    DocumentBatchDelete,
    DocumentExportRequest,
    ReorganizeRequest,
    DocumentFilter,
    SectionBase,
    TagResponse,
    SectionResponse,
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/documents", tags=["整理结果"])


def is_loopback_host(host: Optional[str]) -> bool:
    return host in {"localhost", "127.0.0.1", "::1"}


def request_from_local_browser(request: Request) -> bool:
    origin = request.headers.get("origin") or request.headers.get("referer") or ""
    if origin:
        parsed = urlparse(origin)
        return is_loopback_host(parsed.hostname)

    host = request.client.host if request.client else ""
    return is_loopback_host(host)


def source_path_to_static_url(source_path: str) -> Optional[str]:
    if not source_path:
        return None

    p = Path(source_path)
    if not p.exists():
        return None

    try:
        parts = p.parts
        uploads_idx = None
        for i, part in enumerate(parts):
            if part == "uploads":
                uploads_idx = i
                break
        if uploads_idx is not None and uploads_idx + 1 < len(parts):
            relative = "/".join(parts[uploads_idx + 1:])
            return f"/static/uploads/{relative}"
    except Exception:
        return None

    return None


def parse_location_target(location: Optional[str]) -> dict:
    page_number = None
    video_start = None
    video_end = None

    if location:
        page_patterns = [
            r"第\s*(\d+)\s*(?:[-~—–至到]\s*\d+\s*)?页",
            r"页码\s*[:：]?\s*(\d+)",
            r"(?:page|p\.)\s*(\d+)",
        ]
        for pattern in page_patterns:
            page_match = re.search(pattern, location, flags=re.IGNORECASE)
            if page_match:
                page_number = int(page_match.group(1))
                break

        time_match = re.search(r"(\d+\.?\d*)\s*s\s*-\s*(\d+\.?\d*)\s*s", location)
        if time_match:
            video_start = float(time_match.group(1))
            video_end = float(time_match.group(2))
        else:
            single_time_match = re.search(r"(\d+\.?\d*)\s*s", location)
            if single_time_match:
                video_start = float(single_time_match.group(1))

    return {
        "page_number": page_number,
        "video_start": video_start,
        "video_end": video_end,
    }


def get_pdf_page_count(file_path: Path) -> Optional[int]:
    try:
        import fitz

        with fitz.open(str(file_path)) as pdf:
            return len(pdf)
    except Exception:
        return None


def estimate_page_from_location(location: Optional[str], page_count: Optional[int]) -> Optional[int]:
    if not location or not page_count or page_count < 1:
        return None

    text = location.strip()
    vague_positions = [
        (r"(开头|开始|起始|前部|前半|前半部分|前面|前文|文档前部|上半部分)", 0.15),
        (r"(中部|中间|中段|中间部分|文档中部|正文中部)", 0.50),
        (r"(后部|后半|后半部分|后面|后文|文档后部|下半部分)", 0.75),
        (r"(结尾|末尾|尾部|最后|文末|文档结尾|结束部分)", 1.00),
    ]
    for pattern, ratio in vague_positions:
        if re.search(pattern, text):
            return max(1, min(page_count, round(page_count * ratio)))

    return None


def resolve_pdf_page_number(
    file_path: Path,
    doc_type: str,
    location: Optional[str],
    current_page: Optional[int],
) -> Optional[int]:
    if current_page or not is_pdf_document(file_path, doc_type):
        return current_page

    page_count = get_pdf_page_count(file_path)
    return estimate_page_from_location(location, page_count)


def find_sumatra_pdf() -> Optional[str]:
    candidates = [
        os.environ.get("SUMATRA_PDF_PATH", ""),
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.expandvars(r"%LocalAppData%\SumatraPDF\SumatraPDF.exe"),
        os.path.expandvars(r"%UserProfile%\AppData\Local\SumatraPDF\SumatraPDF.exe"),
        os.path.expandvars(r"%UserProfile%\scoop\apps\sumatrapdf\current\SumatraPDF.exe"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def is_pdf_document(file_path: Path, doc_type: str) -> bool:
    return file_path.suffix.lower() == ".pdf" or doc_type.lower() == "pdf"


def escape_dde_string(value: str) -> str:
    return value.replace('"', '\\"')


def send_sumatra_dde(sumatra_exe: str, file_path: Path, page_number: int) -> tuple[bool, list[str]]:
    escaped_path = escape_dde_string(str(file_path))
    dde_command = f'[GotoPage("{escaped_path}",{page_number})]'
    command = [sumatra_exe, "-dde", dde_command]

    try:
        subprocess.run(
            command,
            timeout=3,
            check=False,
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True, command
    except Exception:
        return False, command


def open_pdf_with_sumatra(file_path: Path, page_number: Optional[int]) -> tuple[bool, Optional[str], dict[str, Any]]:
    if platform.system() != "Windows":
        return False, "SumatraPDF 定位打开仅支持 Windows", {}

    sumatra_exe = find_sumatra_pdf()
    if not sumatra_exe:
        return False, (
            "未找到 SumatraPDF。请安装 SumatraPDF，或设置环境变量 "
            "SUMATRA_PDF_PATH 指向 SumatraPDF.exe"
        ), {}

    command = [sumatra_exe, "-reuse-instance", str(file_path)]

    subprocess.Popen(command)
    command_info: dict[str, Any] = {
        "open": command,
        "dde": None,
        "retry": None,
    }

    if page_number:
        time.sleep(0.45)
        dde_ok, dde_command = send_sumatra_dde(sumatra_exe, file_path, page_number)
        command_info["dde"] = dde_command

        if not dde_ok:
            retry_command = [sumatra_exe, "-reuse-instance", "-page", str(page_number), str(file_path)]
            subprocess.Popen(retry_command)
            command_info["retry"] = retry_command

    return True, None, command_info


def build_sumatra_pdf_error() -> str:
    checked_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.expandvars(r"%LocalAppData%\SumatraPDF\SumatraPDF.exe"),
        os.path.expandvars(r"%UserProfile%\scoop\apps\sumatrapdf\current\SumatraPDF.exe"),
    ]
    return (
        "PDF 文件已禁止使用系统默认程序打开，避免被 WPS 接管；"
        "但当前没有找到 SumatraPDF。请安装 SumatraPDF，或设置 SUMATRA_PDF_PATH。"
        f"已检查路径：{'; '.join(checked_paths)}"
    )


@router.get("", response_model=ApiResponse)
async def list_documents(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    category: Optional[str] = Query(None, description="分类筛选"),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取整理结果列表（分页+筛选）"""
    stmt = select(Document).options(selectinload(Document.tags))

    # 筛选条件
    if keyword:
        stmt = stmt.where(
            (Document.title.contains(keyword)) |
            (Document.original_title.contains(keyword)) |
            (Document.summary.contains(keyword))
        )
    if category:
        stmt = stmt.where(Document.category == category)
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)
    if tag:
        stmt = stmt.join(document_tag_table).join(Tag).where(Tag.name == tag)

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页
    stmt = stmt.order_by(Document.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    docs = result.scalars().all()

    items = []
    for doc in docs:
        # 摘要截断
        summary = doc.summary[:100] + "..." if len(doc.summary) > 100 else doc.summary
        items.append(DocumentListItem(
            id=doc.id,
            title=doc.title,
            original_title=doc.original_title,
            doc_type=doc.doc_type,
            source_path=doc.source_path,
            source_url=doc.source_url,
            char_count=doc.char_count,
            category=doc.category,
            summary=summary,
            method=doc.method,
            model=doc.model,
            tags=[TagResponse(id=t.id, name=t.name) for t in doc.tags],
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        ))

    paginated = PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )

    return ApiResponse(code=0, data=paginated, message="success")


@router.get("/{document_id}", response_model=ApiResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取单条整理结果详情"""
    stmt = select(Document).where(Document.id == document_id).options(
        selectinload(Document.sections),
        selectinload(Document.tags),
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc_resp = DocumentResponse(
        id=doc.id,
        title=doc.title,
        original_title=doc.original_title,
        doc_type=doc.doc_type,
        source_path=doc.source_path,
        source_url=doc.source_url,
        char_count=doc.char_count,
        ai_file_reading=doc.ai_file_reading,
        method=doc.method,
        model=doc.model,
        category=doc.category,
        summary=doc.summary,
        overall_evaluation=doc.overall_evaluation,
        title_suggestion=doc.title_suggestion,
        reason=doc.reason,
        search_text=doc.search_text,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        sections=[SectionResponse(
            id=s.id, document_id=s.document_id,
            section_title=s.section_title, location_hint=s.location_hint,
            summary=s.summary, search_text=s.search_text, created_at=s.created_at,
        ) for s in doc.sections],
        tags=[TagResponse(id=t.id, name=t.name) for t in doc.tags],
    )

    return ApiResponse(code=0, data=doc_resp, message="success")


@router.put("/{document_id}", response_model=ApiResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新整理结果"""
    stmt = select(Document).where(Document.id == document_id).options(selectinload(Document.tags))
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 更新字段
    if update_data.title is not None:
        doc.title = update_data.title
    if update_data.category is not None:
        doc.category = update_data.category
    if update_data.summary is not None:
        doc.summary = update_data.summary
    if update_data.overall_evaluation is not None:
        doc.overall_evaluation = update_data.overall_evaluation
    if update_data.title_suggestion is not None:
        doc.title_suggestion = update_data.title_suggestion
    if update_data.reason is not None:
        doc.reason = update_data.reason
    if update_data.search_text is not None:
        doc.search_text = update_data.search_text

    # 更新标签
    if update_data.tags is not None:
        # 删除旧标签关联
        await db.execute(
            delete(document_tag_table).where(document_tag_table.c.document_id == document_id)
        )
        # 添加新标签
        for tag_name in update_data.tags:
            tag_stmt = select(Tag).where(Tag.name == tag_name)
            tag_result = await db.execute(tag_stmt)
            tag = tag_result.scalar_one_or_none()
            if tag is None:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            await db.execute(
                document_tag_table.insert().values(document_id=document_id, tag_id=tag.id)
            )

    await db.commit()

    return ApiResponse(code=0, data={"id": document_id}, message="更新成功")


@router.delete("/{document_id}", response_model=ApiResponse)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """删除整理结果"""
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    await db.delete(doc)
    await db.commit()

    return ApiResponse(code=0, data=None, message="删除成功")


@router.delete("/batch", response_model=ApiResponse)
async def batch_delete_documents(
    request: DocumentBatchDelete,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """批量删除整理结果"""
    stmt = select(Document).where(Document.id.in_(request.ids))
    result = await db.execute(stmt)
    docs = result.scalars().all()

    for doc in docs:
        await db.delete(doc)

    await db.commit()

    return ApiResponse(code=0, data={"deleted_count": len(docs)}, message=f"已删除 {len(docs)} 条记录")


@router.post("/{document_id}/reorganize", response_model=ApiResponse)
async def reorganize_document(
    document_id: int,
    request: ReorganizeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """重新整理单条文档"""
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    from app.workers.process_worker import start_process_task
    import asyncio

    task = await task_manager.create_task(
        db, task_type="file_process",
        message=f"重新整理文档: {doc.title}",
    )

    aio_task = asyncio.create_task(
        start_process_task(task.id, [document_id], request.provider)
    )
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(code=0, data={"task_id": task.id}, message="重新整理任务已创建")


@router.post("/export", response_model=ApiResponse)
async def export_documents(
    request: DocumentExportRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """导出整理结果为 JSON"""
    stmt = select(Document).options(selectinload(Document.sections), selectinload(Document.tags))

    if request.ids:
        stmt = stmt.where(Document.id.in_(request.ids))
    if request.category:
        stmt = stmt.where(Document.category == request.category)

    result = await db.execute(stmt)
    docs = result.scalars().all()

    export_data = []
    for doc in docs:
        export_data.append({
            "document": {
                "type": doc.doc_type,
                "title": doc.original_title,
                "path": doc.source_path,
                "url": doc.source_url,
                "char_count": doc.char_count,
                "ai_file_reading": doc.ai_file_reading,
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
        })

    return ApiResponse(code=0, data=export_data, message=f"已导出 {len(export_data)} 条记录")


@router.get("/{document_id}/file-url", response_model=ApiResponse)
async def get_document_file_url(
    document_id: int,
    location: Optional[str] = Query(None, description="搜索结果中的位置信息，如'第 3 页'或'12.50s - 35.00s'"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取文档文件的访问 URL 和定位信息

    根据 source_path 生成可访问的静态文件 URL，
    并根据 location 信息解析出 PDF 页码或视频时间点。
    """
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    source_path = doc.source_path or ""
    source_url = doc.source_url or ""
    doc_type = doc.doc_type or "unknown"

    target = parse_location_target(location)

    # 解析文件 URL
    file_url = None
    if source_path:
        p = Path(source_path)
        if p.exists():
            target["page_number"] = resolve_pdf_page_number(
                p,
                doc_type,
                location,
                target["page_number"],
            )
            # 将文件系统路径转换为静态文件 URL
            # source_path 形如: ./data/uploads/2025-06/filename_123456.pdf
            # 需要截取 uploads/ 之后的部分
            try:
                # 找到 uploads 之后的相对路径
                parts = p.parts
                uploads_idx = None
                for i, part in enumerate(parts):
                    if part == "uploads":
                        uploads_idx = i
                        break
                if uploads_idx is not None and uploads_idx + 1 < len(parts):
                    relative = "/".join(parts[uploads_idx + 1:])
                    file_url = f"/static/uploads/{relative}"
            except Exception:
                pass

    result_data = {
        "document_id": document_id,
        "doc_type": doc_type,
        "title": doc.title or doc.original_title,
        "source_path": source_path,
        "source_url": source_url,
        "file_url": file_url,
        "location": location,
        "page_number": target["page_number"],
        "video_start": target["video_start"],
        "video_end": target["video_end"],
        "is_available": file_url is not None or bool(source_url),
    }

    return ApiResponse(code=0, data=result_data, message="success")


@router.post("/{document_id}/open-locally", response_model=ApiResponse)
async def open_document_locally(
    request: Request,
    document_id: int,
    location: Optional[str] = Query(None, description="搜索结果中的位置信息，如'第 3 页'或'12.50s - 35.00s'"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    在本地用系统默认应用打开文件

    如果是本地文件路径，用 os.startfile / open / xdg-open 打开。
    如果是 URL，返回 URL 让前端打开。
    """
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    source_path = doc.source_path or ""
    source_url = doc.source_url or ""
    doc_type = doc.doc_type or "unknown"
    target = parse_location_target(location)

    if not request_from_local_browser(request):
        if source_path:
            file_path = Path(source_path)
            if file_path.exists():
                target["page_number"] = resolve_pdf_page_number(
                    file_path,
                    doc_type,
                    location,
                    target["page_number"],
                )
                file_url = source_path_to_static_url(source_path)
                if file_url:
                    return ApiResponse(code=0, data={
                        "opened": False,
                        "method": "browser_preview",
                        "url": file_url,
                        "doc_type": doc_type,
                        "location": location,
                        "page_number": target["page_number"],
                    }, message="远程设备使用浏览器预览")

        if source_url and source_url.startswith("http"):
            return ApiResponse(code=0, data={
                "opened": False,
                "method": "url",
                "url": source_url,
                "doc_type": doc_type,
                "location": location,
                "page_number": target["page_number"],
            }, message="远程设备打开来源链接")

    # 优先打开本地文件
    if source_path:
        file_path = Path(source_path)
        if file_path.exists():
            try:
                system = platform.system()
                if is_pdf_document(file_path, doc_type):
                    target["page_number"] = resolve_pdf_page_number(
                        file_path,
                        doc_type,
                        location,
                        target["page_number"],
                    )
                    opened, error, command = open_pdf_with_sumatra(file_path, target["page_number"])
                    if not opened:
                        raise HTTPException(status_code=500, detail=error or build_sumatra_pdf_error())

                    return ApiResponse(code=0, data={
                        "opened": True,
                        "method": "sumatra_pdf",
                        "path": str(file_path),
                        "doc_type": doc_type,
                        "location": location,
                        "page_number": target["page_number"],
                        "sumatra_command": command,
                    }, message=(
                        f"PDF 已用 SumatraPDF 打开到第 {target['page_number']} 页"
                        if target["page_number"]
                        else "PDF 已用 SumatraPDF 打开"
                    ))

                if system == "Windows":
                    os.startfile(str(file_path))
                elif system == "Darwin":
                    subprocess.Popen(["open", str(file_path)])
                else:
                    subprocess.Popen(["xdg-open", str(file_path)])

                return ApiResponse(code=0, data={
                    "opened": True,
                    "method": "local_file",
                    "path": str(file_path),
                    "doc_type": doc_type,
                    "page_number": target["page_number"],
                }, message="文件已打开")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"打开文件失败: {str(e)}")

    # 如果是 URL，返回 URL 信息
    if source_url and source_url.startswith("http"):
        return ApiResponse(code=0, data={
            "opened": False,
            "method": "url",
            "url": source_url,
            "doc_type": doc_type,
        }, message="文件为在线资源，请在前端打开链接")

    raise HTTPException(status_code=404, detail="文件不存在或路径无效")
