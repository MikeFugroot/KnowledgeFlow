# -*- coding: utf-8 -*-
"""
文件上传路由 — POST /api/upload/files, POST /api/upload/process
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.models.document import Document
from app.schemas.upload import UploadResponse, UploadFileInfo, ProcessRequest, ProcessResponse
from app.schemas.common import ApiResponse
from app.utils.file_storage import generate_upload_path, ensure_all_dirs
from app.utils.text import safe_filename

router = APIRouter(prefix="/api/upload", tags=["文件上传"])


@router.post("/files", response_model=ApiResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    批量上传文件（multipart）

    将文件保存到 uploads/ 目录，并创建 Document 记录
    """
    ensure_all_dirs()
    document_ids = []
    file_infos = []

    for upload_file in files:
        filename = upload_file.filename or "unknown"
        ext = Path(filename).suffix.lower()

        # 验证文件类型
        if ext not in settings.supported_exts_set:
            raise HTTPException(
                status_code=400,
                detail=f"文件类型不支持: {ext}，支持类型: {', '.join(sorted(settings.supported_exts_set))}",
            )

        # 生成存储路径
        dest_path = generate_upload_path(filename)

        # 保存文件
        try:
            with open(dest_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

        # 判断文档类型
        doc_type = ext.lstrip(".")
        if ext in settings.video_exts_set:
            doc_type = "video"

        # 创建 Document 记录
        doc = Document(
            title=safe_filename(Path(filename).stem),
            original_title=filename,
            doc_type=doc_type,
            source_path=str(dest_path),
            char_count=0,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        document_ids.append(doc.id)
        file_infos.append(UploadFileInfo(
            filename=filename,
            file_size=len(content) if content else 0,
            doc_type=doc_type,
            file_path=str(dest_path),
        ))

    return ApiResponse(
        code=0,
        data=UploadResponse(document_ids=document_ids, files=file_infos),
        message=f"成功上传 {len(document_ids)} 个文件",
    )


@router.post("/process", response_model=ApiResponse)
async def process_files(
    request: ProcessRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    触发文件处理（解析+LLM整理）

    创建后台任务，异步处理指定文档
    """
    from app.services.task_manager import task_manager
    from app.workers.process_worker import start_process_task

    # 验证文档存在
    from sqlalchemy import select
    stmt = select(Document).where(Document.id.in_(request.document_ids))
    result = await db.execute(stmt)
    docs = result.scalars().all()

    if not docs:
        raise HTTPException(status_code=404, detail="未找到指定文档")

    # 创建后台任务
    task = await task_manager.create_task(
        db, task_type="file_process",
        message=f"准备处理 {len(docs)} 个文件",
    )

    # 启动异步处理
    import asyncio
    aio_task = asyncio.create_task(
        start_process_task(task.id, request.document_ids, request.provider)
    )
    task_manager.register_asyncio_task(task.id, aio_task)
    aio_task.add_done_callback(lambda t: task_manager.unregister_asyncio_task(task.id))

    return ApiResponse(
        code=0,
        data=ProcessResponse(task_id=task.id, message="任务已创建"),
        message="success",
    )
