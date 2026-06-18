# -*- coding: utf-8 -*-
"""
系统配置相关 Pydantic Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConfigItem(BaseModel):
    """单个配置项"""
    key: str
    value: str = Field(default="", description="配置值（解密后的明文）")
    value_type: str = Field(default="string")
    description: str = Field(default="")
    is_sensitive: bool = Field(default=False, description="是否为敏感配置")


class ConfigUpdateRequest(BaseModel):
    """批量更新配置请求"""
    configs: List[ConfigItem] = Field(..., min_length=1)


class ConfigResponse(BaseModel):
    """配置响应"""
    configs: List[ConfigItem] = Field(default_factory=list)


class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_documents: int = 0
    total_sections: int = 0
    total_tags: int = 0
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    type_distribution: Dict[str, int] = Field(default_factory=dict)
    recent_documents: List[Dict[str, Any]] = Field(default_factory=list)
    index_ready: bool = False
    has_profile: bool = False
