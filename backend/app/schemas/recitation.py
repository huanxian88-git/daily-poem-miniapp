"""背诵相关 Schema：请求/响应模型定义"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- 请求模型 ----

class RecitationStartRequest(BaseModel):
    """开始背诵请求"""
    poem_id: str = Field(..., description="诗词ID")
    confirmed: bool = Field(default=False, description="是否确认继续（并发守卫时使用）")


class FillCheckRequest(BaseModel):
    """补阙填词检查请求"""
    answers: list[dict[str, int | str]] = Field(
        ...,
        description="用户填写的答案列表，每项包含 pos(位置) 和 word(填写的字)",
        examples=[{"pos": 0, "word": "月"}],
    )


class SortCheckRequest(BaseModel):
    """排序归位检查请求"""
    order: list[int] = Field(
        ...,
        description="用户排列的行索引顺序",
        example=[2, 0, 1, 3],
    )


# ---- 响应模型 ----

class RecitationStartResponse(BaseModel):
    """开始背诵响应"""
    recitation_id: str = Field(..., description="背诵记录ID")
    stage: str = Field(default="fill", description="当前阶段")
    warm_reminder: Optional[bool] = Field(
        default=None, description="是否触发了并发提醒（True=提醒但允许，None=无提醒）"
    )


class FillCheckResponse(BaseModel):
    """补阙填词检查结果"""
    model_config = ConfigDict(populate_by_name=True)

    score: int = Field(..., ge=0, le=100, description="得分 0-100")
    pass_: bool = Field(..., alias="pass", description="是否通过（>=60分）")
    detail: dict = Field(default_factory=dict, description="详细评分信息")


class SortCheckResponse(BaseModel):
    """排序归位检查结果"""
    model_config = ConfigDict(populate_by_name=True)

    score: int = Field(..., ge=0, le=100, description="得分 0-100")
    pass_: bool = Field(..., alias="pass", description="是否通过（>=60分）")
    detail: dict = Field(default_factory=dict, description="详细评分信息")


class VoiceCheckResponse(BaseModel):
    """语音背诵检查结果（阶段3 mock版）"""
    score: int = Field(..., ge=0, le=100, description="得分 0-100")
    detail: dict = Field(default_factory=dict, description="详细评分信息")
    recognized_text: Optional[str] = Field(
        default=None, description="ASR识别出的文本（阶段3为传入值回显）"
    )


class RecitationResultResponse(BaseModel):
    """背诵完整结果（三关总览）"""
    recitation_id: str
    poem_id: str
    poem_title: str
    status: str
    is_mastered: bool
    fill_score: Optional[int] = None
    sort_score: Optional[int] = None
    voice_score: Optional[int] = None
    mastered_at: Optional[str] = None
    created_at: str


class RecitationBrief(BaseModel):
    """背诵记录简要信息（列表用）"""
    id: str
    poem_id: str
    poem_title: str
    status: str
    scores: dict = Field(default_factory=dict, description="{fill, sort, voice} 三关得分")
    created_at: str


class RecitationListResponse(BaseModel):
    """在背列表响应"""
    items: list[RecitationBrief]
    total: int
