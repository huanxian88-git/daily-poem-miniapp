"""事件/节日模型：Festival"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class Festival(Base):
    """节日/节气/事件基础数据"""

    __tablename__ = "festivals"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # 日期规则：G:03-21（公历），L:01-01（农历），S:清明（节气）
    date_rule: Mapped[str] = mapped_column(String(64), nullable=False)

    # 关联标签：格式同 Poem.tags
    poem_tags: Mapped[str | None] = mapped_column(Text)

    # 事件等级
    event_level: Mapped[str] = mapped_column(String(10))  # L1/L2/L3/L4/L4b/L5/L6/L7

    # 事件子类型
    event_sub_type: Mapped[str | None] = mapped_column(
        String(20)
    )  # emotion/life/nature/culture

    # 事件描述
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Festival(name={self.name}, level={self.event_level})>"
