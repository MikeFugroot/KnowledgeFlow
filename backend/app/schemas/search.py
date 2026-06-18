# -*- coding: utf-8 -*-
"""
检索相关 Pydantic Schema
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """语义检索请求"""
    query: str = Field(..., min_length=1, description="检索查询词")
    top_k: int = Field(default=8, ge=1, le=50, description="返回结果数")


class SearchHit(BaseModel):
    """单个检索命中结果"""
    rank: int = Field(default=0, description="排名")
    doc_title: str = Field(default="", description="文档标题")
    doc_type: str = Field(default="", description="文档类型")
    source: str = Field(default="", description="来源路径/URL")
    location: str = Field(default="", description="位置提示")
    section_title: str = Field(default="", description="章节标题")
    chunk_text: str = Field(default="", description="命中文本块")
    score: float = Field(default=0.0, description="综合得分")
    dense_score: float = Field(default=0.0, description="向量检索得分")
    lexical_score: float = Field(default=0.0, description="关键词检索得分")
    match_reason: str = Field(default="", description="命中原因")
    hit_terms: List[str] = Field(default_factory=list, description="命中的关键词")
    document_id: Optional[int] = Field(default=None, description="文档ID，用于打开文件")


class SearchResponse(BaseModel):
    """检索响应"""
    query: str
    total: int
    results: List[SearchHit]


class IndexStatusResponse(BaseModel):
    """索引状态响应"""
    is_ready: bool = Field(default=False, description="索引是否就绪")
    total_chunks: int = Field(default=0, description="索引中的文本块数")
    total_documents: int = Field(default=0, description="已索引文档数")
    last_built_at: Optional[str] = Field(default=None, description="上次构建时间")
    embedding_model: str = Field(default="", description="当前使用的embedding模型")
