"""背诵相关模型：Recitation + RecitationStep"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recitation(Base):
    """背诵记录主表"""

    __tablename__ = "recitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    poem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("poems.id"), index=True, nullable=False
    )

    # 背诵状态
    status: Mapped[str] = mapped_column(
        String(20), default="reciting", index=True
    )  # "reciting" | "memorized" | "reviewing" | "favorited"

    # 当前关卡阶段
    current_stage: Mapped[int] = mapped_column(Integer, default=0)
    # 0=未开始, 1=初读, 2=熟读, 3=成诵

    # 是否已完全掌握
    is_mastered: Mapped[bool] = mapped_column(default=False)

    # 总分（三关加权）
    total_score: Mapped[float | None] = mapped_column(Float)

    # 背诵发起时间 & 截止时间
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    deadline: Mapped[datetime | None] = mapped_column(DateTime)

    # 完成/通过时间
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="recitations")
    poem: Mapped["Poem"] = relationship(back_populates="recitations")
    steps: Mapped[list["RecitationStep"]] = relationship(
        back_populates="recitation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Recitation(user={self.user_id}, poem={self.poem_id}, stage={self.current_stage})>"


class RecitationStep(Base):
    """背诵步骤记录：每关的详细结果"""

    __tablename__ = "recitation_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recitation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recitations.id"), index=True, nullable=False
    )

    # 步骤类型
    step_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "fill_blanks" | "sort" | "voice"

    # 步骤序号（第几次尝试）
    attempt: Mapped[int] = mapped_column(Integer, default=1)

    # 得分（该步骤单项分）
    score: Mapped[float | None] = mapped_column(Float)

    # 详细结果（JSON：字级比对详情/排序顺序/语音识别文字）
    detail: Mapped[dict | None] = mapped_column(JSONB)

    # 耗时（秒）
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer)

    # 是否通过
    is_passed: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联
    recitation: Mapped["Recitation"] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<RecitationStep(recitation={self.recitation_id}, type={self.step_type}, score={self.score})>"


# 延迟导入
from app.models.user import User  # noqa: E402, F811
from app.models.poem import Poem  # noqa: E402, F811
