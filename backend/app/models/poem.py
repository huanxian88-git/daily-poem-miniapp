"""诗词相关模型：Poem"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class Poem(Base):
    """诗词主表"""

    __tablename__ = "poems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    title: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    author: Mapped[str | None] = mapped_column(String(64), index=True)
    dynasty: Mapped[str | None] = mapped_column(String(32))

    # 正文/按句分行/注释/译文/背景
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_lines: Mapped[str | None] = mapped_column(Text)  # JSON数组字符串
    annotation: Mapped[str | None] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text)
    background: Mapped[str | None] = mapped_column(Text)

    # 难度（1-3）
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    # 结构化标签：意象:月,意象:春雨|主题:思乡|场景:清明
    tags: Mapped[str | None] = mapped_column(Text)

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

    def __repr__(self) -> str:
        return f"<Poem(title={self.title}, author={self.author})>"
