"""数据库连接层：SQLAlchemy async engine + session 管理"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 异步引擎（SQLite 不支持连接池参数，需条件判断）
_engine_kwargs = dict(echo=settings.DEBUG, pool_pre_ping=True)
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# 异步 Session 工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 声明式基类
class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
