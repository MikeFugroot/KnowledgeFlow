# -*- coding: utf-8 -*-
"""
网页导入相关 Pydantic Schema
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class UrlImportRequest(BaseModel):
    """单个URL导入请求"""
    url: str = Field(..., min_length=1, description="导入的URL")
    provider: str = Field(default="qwen", description="LLM提供者")


class BatchUrlImportRequest(BaseModel):
    """批量URL导入请求"""
    urls: List[str] = Field(..., min_length=1, description="URL列表")
    provider: str = Field(default="qwen", description="LLM提供者")


class BilibiliFavoritesRequest(BaseModel):
    """B站收藏夹导入请求"""
    folder_id: int = Field(..., description="收藏夹ID")
    max_videos: int = Field(default=20, ge=1, le=100, description="最大导入数")
    provider: str = Field(default="qwen", description="LLM提供者")


class BookmarkImportRequest(BaseModel):
    """书签HTML导入请求"""
    bookmark_path: str = Field(..., description="书签HTML文件路径")
    max_links: int = Field(default=50, ge=1, le=500, description="最大导入链接数")
    provider: str = Field(default="qwen", description="LLM提供者")


class BilibiliFolderItem(BaseModel):
    """B站收藏夹项"""
    folder_id: int
    title: str = ""
    media_count: int = 0
    intro: str = ""
    is_public: bool = True


class CookieTestRequest(BaseModel):
    """Cookie测试请求"""
    cookie: str = Field(..., min_length=1, description="Cookie字符串")


class CookieTestResponse(BaseModel):
    """Cookie测试响应"""
    success: bool
    message: str = ""
