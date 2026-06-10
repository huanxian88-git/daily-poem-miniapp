"""事件/节日模型"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Festival(Base):
    """节日/节气基础数据"""

    __tablename__ = "festivals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    category: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False
    )  # "traditional" | "solar_term" | "cultural" | "modern"
    lunar_date: Mapped[str | None] = mapped_column(String(32))
    solar_date: Mapped[str | None] = mapped_column(String(32))

    # 描述
    description: Mapped[str | None] = mapped_column(Text)

    # 优先级（推荐权重）
    priority: Mapped[int] = mapped_column(Integer, default=5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Festival(name={self.name}, category={self.category})>"


class CalendarEvent(Base):
    """365天日历映射表"""

    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)

    # 关联的节日/节气/纪念日（JSON数组）
    events: Mapped[dict | None] = mapped_column(  # type: ignore
        "events_json"
    )  # [{"type":"festival","name":"春节","priority":10},...]

    # 季节
    season: Mapped[str | None] = mapped_column(String(16))  # "spring"|"summer"|...

    # 月份
    month: Mapped[int] = mapped_column(Integer, index=True)
    day: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CalendarEvent(date={self.event_date}, season={self.season})>"
