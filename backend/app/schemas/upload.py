# -*- coding: utf-8 -*-
"""
文件上传相关 Pydantic Schema
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class UploadFileInfo(BaseModel):
    """上传文件信息"""
    filename: str
    file_size: int = 0
    doc_type: str = ""
    file_path: str = ""


class UploadResponse(BaseModel):
    """上传响应"""
    document_ids: List[int] = Field(default_factory=list, description="创建的文档ID列表")
    files: List[UploadFileInfo] = Field(default_factory=list)


class ProcessRequest(BaseModel):
    """触发文件处理请求"""
    document_ids: List[int] = Field(..., min_length=1, description="待处理的文档ID列表")
    provider: str = Field(default="qwen", description="LLM提供者: qwen/deepseek")


class ProcessResponse(BaseModel):
    """处理响应"""
    task_id: int = Field(..., description="后台任务ID")
    message: str = "任务已创建"
