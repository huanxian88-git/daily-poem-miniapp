"""每日推荐 Schema"""

from pydantic import BaseModel

from app.schemas.poem import PoemDetail


class DailyTodayResponse(BaseModel):
    poem: PoemDetail
    reason: str
    reason_type: str | None = None
    can_switch: bool = True
    switch_count: int = 0  # 今日已换次数


class DailySwitchResponse(BaseModel):
    poem: PoemDetail
    reason: str
    reason_type: str | None = None
    can_switch: bool = True
    switch_count: int = 0
