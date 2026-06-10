"""用户相关模型：User + UserProfile"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """微信用户基础表"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    unionid: Mapped[str | None] = mapped_column(String(128), index=True)
    nickname: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)  # 2期预留
    ban_reason: Mapped[str | None] = mapped_column(Text)  # 2期预留

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    # 关联
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    recitations: Mapped[list["Recitation"]] = relationship(back_populates="user")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    review_schedules: Mapped[list["ReviewSchedule"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname})>"


class UserProfile(Base):
    """用户画像：偏好/水平/课本绑定"""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # 年龄段
    age_group: Mapped[str | None] = mapped_column(
        Enum("under_12", "12_18", "18_25", "25_35", "35_50", "over_50",
             name="age_group_enum", create_type=False)
    )

    # 诗词水平
    level: Mapped[str | None] = mapped_column(
        Enum("beginner", "intermediate", "advanced",
             name="poem_level_enum", create_type=False)
    )

    # 兴趣偏好（JSON 数组存储）
    interests: Mapped[str | None] = mapped_column(Text)  # ["山水","送别","边塞",...]

    # 背诵节奏
    recite_rhythm: Mapped[str] = mapped_column(
        String(20), default="every_2_days"
    )
    recite_rhythm_custom_days: Mapped[int | None] = mapped_column(Integer)

    # 课本绑定
    textbook_version: Mapped[str | None] = mapped_column(String(64))  # "人教版"
    textbook_grade: Mapped[int | None] = mapped_column(Integer)  # 3
    textbook_semester: Mapped[str | None] = mapped_column(String(10))  # "上学期"

    # 是否为学生（影响课本卡片展示）
    is_student: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, level={self.level})>"
