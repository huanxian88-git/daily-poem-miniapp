"""复习相关 Schema：请求/响应模型定义"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ReviewQueueItem(BaseModel):
    """复习队列项"""
    poem_id: str
    poem_title: str
    next_review_date: date
    review_count: int = Field(description="已复习次数")
    urgency: str = Field(description="紧急程度：high/medium/low")


class ReviewQueueResponse(BaseModel):
    """复习队列响应"""
    items: list[ReviewQueueItem]
    total: int


class ReviewDoneRequest(BaseModel):
    """标记复习完成请求"""
    self_assessment: str = Field(
        ...,
        description="自评难度：easy=简单 good=一般 hard=困难",
        pattern=r"^(easy|good|hard)$",
    )


class ReviewDoneResponse(BaseModel):
    """标记复习完成响应"""
    next_review_date: date
    interval_days: int = Field(description="距下次复习的间隔天数")


class ReviewStatsResponse(BaseModel):
    """复习统计响应"""
    total: int = Field(description="总复习计划数")
    mastered: int = Field(description="已掌握数")
    reviewing: int = Field(description="复习中数")
    today_due: int = Field(description="今日到期需复习数")
