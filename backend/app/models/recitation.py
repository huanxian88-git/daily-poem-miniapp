"""背诵相关模型：Recitation"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class Recitation(Base):
    """背诵记录（用户-诗词关联表）"""

    __tablename__ = "recitations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    poem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("poems.id"), index=True, nullable=False
    )

    # 背诵状态
    status: Mapped[str] = mapped_column(
        String(20), default="reciting", index=True
    )  # "reciting" | "memorized" | "reviewing"

    # 当前阶段
    recite_stage: Mapped[str | None] = mapped_column(String(20))  # 初读/熟读/成诵

    # 三关得分
    fill_score: Mapped[int | None] = mapped_column(Integer)  # 补阙得分
    sort_score: Mapped[int | None] = mapped_column(Integer)  # 排序得分
    voice_score: Mapped[int | None] = mapped_column(Integer)  # 语音得分

    # 尝试次数
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)

    # 是否已完全掌握
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    deadline: Mapped[datetime | None] = mapped_column(DateTime)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Recitation(user={self.user_id}, poem={self.poem_id}, status={self.status})>"
