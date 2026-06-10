"""测试 fixture —— 内存 SQLite + 异步测试客户端。"""

import os

# 在导入 app 之前设置测试环境变量
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("REDIS_GRACEFUL_DEGRADATION", "true")
os.environ.setdefault("JWT_SECRET", "test-ci-secret-key-do-not-use-in-production")
os.environ.setdefault("WECHAT_APPID", "wxcb715f5de1dee100")
os.environ.setdefault("WECHAT_SECRET", "")

from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app

# 测试用内存 SQLite —— 和 app.core.database.engine 共享同一个 URL
# 因为 DATABASE_URL 已经设为 "sqlite+aiosqlite://"，
# app 的引擎也是内存 SQLite，但它们是不同的连接池。
# 我们直接使用 app 的引擎来创建表，避免连接到不同的数据库。
from app.core import database as db_module

test_engine = db_module.engine
test_async_session = db_module.async_session


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """每个测试前创建表，测试后删除表。"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 不再需要 override_get_db，直接用 app 自带的 get_db
# 因为测试引擎就是 app 的引擎（DATABASE_URL 已设为内存 SQLite）


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_token() -> str:
    """生成测试用 access_token。"""
    return create_access_token("1", "test_openid")


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供测试用的数据库 session。"""
    async with test_async_session() as session:
        yield session
