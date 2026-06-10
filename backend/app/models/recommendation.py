"""每日推荐模型"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DailyRecommendation(Base):
    """每日推荐记录"""

    __tablename__ = "daily_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    poem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("poems.id"), index=True, nullable=False
    )
    recommend_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    # 推荐理由
    reason: Mapped[str | None] = mapped_column(Text)
    reason_type: Mapped[str | None] = mapped_column(
        String(32)
    )  # "festival"|"solar_term"|"textbook"|"tag_match"|"manual"

    # 匹配的标签（JSON数组）
    matched_tags: Mapped[dict | None] = mapped_column(  # type: ignore
        "matched_tags_json"
    )

    # 用户反馈
    is_accepted: Mapped[bool | None] = mapped_column(Boolean)  # None=未查看
    is_favorited: Mapped[bool] = mapped_column(Boolean, default=False)

    # 运营相关（2期预留）
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    pin_operator: Mapped[str | None] = mapped_column(String(64))

    # 推荐算法评分明细（JSON）
    score_detail: Mapped[dict | None] = mapped_column(  # type: ignore
        "score_detail_json"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DailyRecommendation(user={self.user_id}, poem={self.poem_id}, date={self.recommend_date})>"
