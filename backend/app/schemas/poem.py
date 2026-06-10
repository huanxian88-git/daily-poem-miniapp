"""Pydantic Schema 定义：API 请求/响应序列化"""

import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ===== 用户 =====

class UserProfileSchema(BaseModel):
    """用户画像 Schema"""
    age_group: Optional[str] = None
    level: Optional[str] = None
    interests: Optional[list[str]] = None
    recite_rhythm: str = "every_2_days"
    recite_rhythm_custom_days: Optional[int] = None
    textbook_version: Optional[str] = None
    textbook_grade: Optional[int] = None
    textbook_semester: Optional[str] = None
    is_student: bool = False

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """用户画像更新"""
    age_group: Optional[str] = None
    level: Optional[str] = None
    interests: Optional[list[str]] = None
    recite_rhythm: Optional[str] = None
    recite_rhythm_custom_days: Optional[int] = None
    textbook_version: Optional[str] = None
    textbook_grade: Optional[int] = None
    textbook_semester: Optional[str] = None
    is_student: Optional[bool] = None


class UserSchema(BaseModel):
    """用户基础信息"""
    id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ===== 诗词 =====

class PoemTagSchema(BaseModel):
    """诗词标签"""
    id: Optional[str] = None
    category: str
    name: str
    weight: float = 1.0

    model_config = {"from_attributes": True}


class PoemBase(BaseModel):
    """诗词基础信息"""
    title: str
    author: str
    dynasty: str
    content: str
    annotation: Optional[str] = None
    translation: Optional[str] = None
    background: Optional[str] = None
    difficulty: int = 3


class PoemListItem(BaseModel):
    """诗词列表项（轻量）"""
    id: str
    title: str
    author: str
    dynasty: str
    difficulty: int
    scene_type: Optional[str] = None
    scene_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class PoemDetail(BaseModel):
    """诗词详情"""
    id: str
    title: str
    author: str
    dynasty: str
    content: str
    annotation: Optional[str] = None
    translation: Optional[str] = None
    background: Optional[str] = None
    difficulty: int
    scene_type: Optional[str] = None
    scene_desc: Optional[str] = None
    scene_image_url: Optional[str] = None
    tags: list[PoemTagSchema] = []
    textbook: Optional[str] = None
    textbook_grade: Optional[int] = None

    model_config = {"from_attributes": True}


# ===== 每日推荐 =====

class DailyRecommendResponse(BaseModel):
    """每日推荐响应"""
    recommend_id: str
    poem: PoemDetail
    reason: Optional[str] = None
    reason_type: Optional[str] = None
    date: date
    can_switch: bool = True  # 是否还能"换一首"


# ===== 背诵 =====

class ReciteStartRequest(BaseModel):
    """开始背诵请求"""
    poem_id: str


class ReciteStepResult(BaseModel):
    """背诵步骤结果"""
    step_type: str  # "fill_blanks" | "sort" | "voice"
    score: float
    is_passed: bool
    detail: Optional[dict] = None
    time_spent_seconds: Optional[int] = None


class ReciteSubmitRequest(BaseModel):
    """提交背诵结果"""
    recitation_id: str
    step: ReciteStepResult


class ReciteResultResponse(BaseModel):
    """背诵总体结果"""
    recitation_id: str
    poem_title: str
    total_score: float
    is_mastered: bool
    steps: list[ReciteStepResult]
    message: str  # 正向反馈话术


# ===== 复习 =====

class ReviewItem(BaseModel):
    """复习项"""
    id: str
    poem_id: str
    poem_title: str
    poem_author: str
    poem_dynasty: str
    scheduled_date: date
    stage: int
    is_completed: bool


# ===== 通用 =====

class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False
