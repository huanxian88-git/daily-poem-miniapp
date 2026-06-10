"""复习相关模型"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReviewSchedule(Base):
    """艾宾浩斯复习调度表"""

    __tablename__ = "review_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    recitation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recitations.id"), index=True, nullable=False
    )

    # 复习阶段（第n次复习）
    stage: Mapped[int] = mapped_column(Integer, default=1)

    # 计划复习日期
    scheduled_date: Mapped[datetime] = mapped_column(DateTime, index=True)

    # 是否已完成
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联
    user: Mapped["User"] = relationship(back_populates="review_schedules")

    def __repr__(self) -> str:
        return f"<ReviewSchedule(user={self.user_id}, stage={self.stage}, date={self.scheduled_date})>"


from app.models.user import User  # noqa: E402
