# -*- coding: utf-8 -*-
"""
后台任务相关 Pydantic Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """后台任务响应"""
    id: int
    task_type: str = Field(description="任务类型")
    status: str = Field(description="任务状态")
    progress: float = Field(default=0.0, description="进度 0~1")
    message: str = Field(default="", description="状态消息")
    result_json: Optional[str] = None
    error: str = Field(default="")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskProgressPayload(BaseModel):
    """任务进度推送载荷"""
    task_id: int
    task_type: str
    current: int = 0
    total: int = 0
    message: str = ""
