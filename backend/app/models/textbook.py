"""课本关联模型：Textbook + PoemTextbook"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import _uuid_str


class Textbook(Base):
    """课本版本基础数据"""

    __tablename__ = "textbooks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # "人教版（统编版）"
    publisher: Mapped[str | None] = mapped_column(String(64))  # "人民教育出版社"
    edition: Mapped[str | None] = mapped_column(String(32))  # "2024年版"

    def __repr__(self) -> str:
        return f"<Textbook(name={self.name})>"


class PoemTextbook(Base):
    """诗词-课本关联表"""

    __tablename__ = "poem_textbooks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid_str
    )
    poem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("poems.id"), index=True, nullable=False
    )
    textbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("textbooks.id"), index=True, nullable=False
    )
    grade: Mapped[int] = mapped_column(Integer)  # 1-12
    semester: Mapped[str] = mapped_column(String(10))  # upper/lower
    unit: Mapped[int | None] = mapped_column(Integer)  # 单元号
    teaching_focus: Mapped[str | None] = mapped_column(String(128))  # 教学重点标签

    def __repr__(self) -> str:
        return f"<PoemTextbook(poem={self.poem_id}, grade={self.grade}, semester={self.semester})>"
