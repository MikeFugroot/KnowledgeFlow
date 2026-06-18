# -*- coding: utf-8 -*-
"""
通用响应模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = Field(default=0, description="错误码，0=成功")
    data: Optional[Any] = Field(default=None, description="响应数据")
    message: str = Field(default="success", description="响应消息")


class PaginatedResponse(BaseModel):
    """分页响应数据"""
    items: List[Any] = Field(default_factory=list)
    total: int = Field(default=0)
    page: int = Field(default=1)
    page_size: int = Field(default=20)
