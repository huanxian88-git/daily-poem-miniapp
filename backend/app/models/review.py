"""复习相关模型：ReviewSchedule"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class ReviewSchedule(Base):
    """艾宾浩斯复习调度表"""

    __tablename__ = "review_schedules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    poem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("poems.id"), index=True, nullable=False
    )

    # 下次复习日期
    next_review_date: Mapped[date | None] = mapped_column(Date, index=True)

    # 已复习次数
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    # 艾宾浩斯核心参数
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)

    # 上次复习时间
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ReviewSchedule(user={self.user_id}, poem={self.poem_id}, next={self.next_review_date})>"
