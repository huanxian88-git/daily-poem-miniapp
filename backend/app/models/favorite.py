"""收藏模型：Favorite"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class Favorite(Base):
    """用户珍藏"""

    __tablename__ = "favorites"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    poem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("poems.id"), index=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Favorite(user={self.user_id}, poem={self.poem_id})>"
