"""诗词相关模型：Poem + PoemTag"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Poem(Base):
    """诗词主表"""

    __tablename__ = "poems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    author: Mapped[str] = mapped_column(String(64), index=True)
    dynasty: Mapped[str] = mapped_column(String(32))

    # 正文/注释/译文/背景
    content: Mapped[str] = mapped_column(Text, nullable=False)
    annotation: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    background: Mapped[str | None] = mapped_column(Text)

    # 难度（1-5星）
    difficulty: Mapped[int] = mapped_column(Integer, default=3)

    # 关联事件（JSON对象）
    related_event: Mapped[dict | None] = mapped_column(JSONB)

    # 课本关联
    textbook: Mapped[str | None] = mapped_column(String(128))
    textbook_grade: Mapped[int | None] = mapped_column(Integer)

    # AI场景类型
    scene_type: Mapped[str | None] = mapped_column(String(64), index=True)
    scene_desc: Mapped[str | None] = mapped_column(Text)

    # 场景图URL（COS）
    scene_image_url: Mapped[str | None] = mapped_column(String(512))

    # 运营相关（2期预留）
    status: Mapped[str] = mapped_column(String(20), default="active")
    audit_note: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="manual")

    # 统计
    recite_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联
    tags: Mapped[list["PoemTag"]] = relationship(back_populates="poem", cascade="all, delete-orphan")
    recitations: Mapped[list["Recitation"]] = relationship(back_populates="poem")

    def __repr__(self) -> str:
        return f"<Poem(title={self.title}, author={self.author})>"


class PoemTag(Base):
    """诗词标签：意象/主题/场景三类"""

    __tablename__ = "poem_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    poem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("poems.id"), index=True
    )

    # 标签类别
    category: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False
    )  # "imagery" | "theme" | "scene"

    # 标签名
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # 权重
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    # 关联
    poem: Mapped["Poem"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return f"<PoemTag(poem_id={self.poem_id}, {self.category}={self.name})>"


# 延迟导入以避免循环引用
from app.models.recitation import Recitation  # noqa: E402, F811
