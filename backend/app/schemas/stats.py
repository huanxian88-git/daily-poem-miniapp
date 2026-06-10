"""统计汇总 Schema"""

from pydantic import BaseModel, Field


class StatsSummaryResponse(BaseModel):
    """学习统计摘要响应"""
    total_recited: int = Field(description="累计背诵诗词总数")
    total_mastered: int = Field(description="累计完全掌握数")
    streak_days: int = Field(description="连续背诵天数")
    today_recited: int = Field(description="今日已背诵数量")
