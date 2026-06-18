# -*- coding: utf-8 -*-
"""
文档相关 Pydantic Schema
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---- Section ----

class SectionBase(BaseModel):
    """章节基础信息"""
    section_title: str = Field(default="", description="章节标题")
    location_hint: str = Field(default="", description="位置提示")
    summary: str = Field(default="", description="章节摘要")
    search_text: str = Field(default="", description="章节语义检索内容")


class SectionResponse(SectionBase):
    """章节响应"""
    id: int
    document_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Tag ----

class TagResponse(BaseModel):
    """标签响应"""
    id: int
    name: str

    model_config = {"from_attributes": True}


# ---- Document ----

class DocumentBase(BaseModel):
    """文档基础信息"""
    title: str = Field(default="", description="整理后标题")
    original_title: str = Field(default="", description="原始标题")
    doc_type: str = Field(default="unknown", description="文档类型")
    source_path: str = Field(default="", description="原始文件路径")
    source_url: str = Field(default="", description="来源URL")
    char_count: int = Field(default=0, description="原始文本字符数")
    ai_file_reading: bool = Field(default=False, description="是否使用AI文件直读")
    method: str = Field(default="", description="整理方法")
    model: str = Field(default="", description="使用的LLM模型名")
    category: str = Field(default="其他", description="分类")
    summary: str = Field(default="", description="整体摘要")
    overall_evaluation: str = Field(default="", description="整体评价")
    title_suggestion: str = Field(default="", description="AI建议标题")
    reason: str = Field(default="", description="分类理由")
    search_text: str = Field(default="", description="全文语义检索内容")


class DocumentCreate(BaseModel):
    """创建文档请求"""
    title: str
    original_title: str = ""
    doc_type: str = "unknown"
    source_path: str = ""
    source_url: str = ""
    char_count: int = 0
    ai_file_reading: bool = False
    method: str = ""
    model: str = ""
    category: str = "其他"
    summary: str = ""
    overall_evaluation: str = ""
    title_suggestion: str = ""
    reason: str = ""
    search_text: str = ""
    tags: List[str] = Field(default_factory=list, description="标签列表")
    sections: List[SectionBase] = Field(default_factory=list, description="章节列表")


class DocumentUpdate(BaseModel):
    """更新文档请求"""
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    overall_evaluation: Optional[str] = None
    title_suggestion: Optional[str] = None
    reason: Optional[str] = None
    search_text: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentResponse(DocumentBase):
    """文档响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    sections: List[SectionResponse] = Field(default_factory=list)
    tags: List[TagResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    """文档列表项（不含大文本字段，用于列表展示）"""
    id: int
    title: str
    original_title: str
    doc_type: str
    source_path: str
    source_url: str
    char_count: int
    category: str
    summary: str = Field(default="", description="摘要截断显示")
    method: str
    model: str
    tags: List[TagResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentFilter(BaseModel):
    """文档筛选参数"""
    keyword: Optional[str] = None
    category: Optional[str] = None
    doc_type: Optional[str] = None
    tag: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class DocumentBatchDelete(BaseModel):
    """批量删除文档"""
    ids: List[int] = Field(..., min_length=1, description="待删除的文档ID列表")


class DocumentExportRequest(BaseModel):
    """导出请求"""
    ids: Optional[List[int]] = None
    category: Optional[str] = None


class ReorganizeRequest(BaseModel):
    """重新整理文档请求"""
    provider: str = Field(default="qwen", description="LLM提供者: qwen/deepseek")
