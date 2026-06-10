"""每日推荐模型：DailyRecommendation"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class DailyRecommendation(Base):
    """每日推荐记录"""

    __tablename__ = "daily_recommendations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    poem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("poems.id"), index=True, nullable=False
    )
    recommend_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    # 推荐理由
    reason: Mapped[str | None] = mapped_column(Text)
    reason_type: Mapped[str | None] = mapped_column(
        String(32)
    )  # "festival"|"solar_term"|"textbook"|"tag_match"|"manual"

    # 匹配的标签（JSON字符串）
    matched_tags: Mapped[str | None] = mapped_column(Text)

    # 运营相关（2期预留）
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DailyRecommendation(poem={self.poem_id}, date={self.recommend_date})>"
