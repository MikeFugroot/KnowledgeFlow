# -*- coding: utf-8 -*-
"""
知识画像相关 Pydantic Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProfileOverview(BaseModel):
    """画像总览"""
    total_documents: int = 0
    knowledge_units: int = 0
    total_chars: int = 0
    main_focus: str = ""
    top_tags: List[str] = Field(default_factory=list)
    dominant_type: str = ""


class TagRankingItem(BaseModel):
    """标签排名项"""
    tag: str
    count: int


class KnowledgeClusterItem(BaseModel):
    """知识聚类项"""
    cluster: str
    score: float = 0.0
    related_items: List[str] = Field(default_factory=list)


class TimelineItem(BaseModel):
    """时间线条目"""
    date: str
    title: str
    category: str
    tags: List[str] = Field(default_factory=list)


class ProfileResponse(BaseModel):
    """画像响应"""
    id: int
    generated_by: str = ""
    total_documents: int = 0
    knowledge_units: int = 0
    main_focus: str = ""
    profile_json: Optional[Dict[str, Any]] = None
    overview: Optional[Dict[str, Any]] = None
    theme_distribution: Optional[Dict[str, int]] = None
    tag_ranking: Optional[List[TagRankingItem]] = None
    knowledge_clusters: Optional[List[KnowledgeClusterItem]] = None
    learning_timeline: Optional[List[TimelineItem]] = None
    knowledge_gaps: Optional[List[str]] = None
    learning_path: Optional[List[str]] = None
    growth_suggestions: Optional[List[str]] = None
    llm_profile: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileStatusResponse(BaseModel):
    """画像生成状态"""
    is_generating: bool = False
    has_profile: bool = False
    last_generated_at: Optional[str] = None
