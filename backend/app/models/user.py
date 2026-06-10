"""用户相关模型：User + UserProfile

兼容 SQLite（开发）和 PostgreSQL（生产）：
- UUID 主键使用 String(36) 存储，避免 PostgreSQL 方言依赖
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid_str():
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


class User(Base):
    """微信用户基础表"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    unionid: Mapped[str | None] = mapped_column(String(128), index=True)
    nickname: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    # 关联
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname})>"


class UserProfile(Base):
    """用户画像：偏好/水平/课本绑定"""

    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, index=True, nullable=False
    )

    # 年龄段
    age_group: Mapped[str | None] = mapped_column(String(20))

    # 诗词水平
    level: Mapped[str | None] = mapped_column(String(20))

    # 兴趣偏好（JSON 数组字符串）
    interests: Mapped[str | None] = mapped_column(Text)

    # 背诵节奏
    recite_rhythm: Mapped[str] = mapped_column(
        String(20), default="every_2_days"
    )
    recite_rhythm_custom_days: Mapped[int | None] = mapped_column(Integer)

    # 课本绑定
    textbook_version: Mapped[str | None] = mapped_column(String(64))
    textbook_grade: Mapped[int | None] = mapped_column(Integer)
    textbook_semester: Mapped[str | None] = mapped_column(String(10))

    # 是否为学生
    is_student: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, level={self.level})>"
