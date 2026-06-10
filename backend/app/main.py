from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis


async def init_db():
    """自动建表（开发环境）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：初始化Redis、自动建表，关闭时释放资源"""
    await init_redis()
    await init_db()
    yield
    await close_redis()


# 确保所有模型被导入（触发 Base 注册）
import app.models  # noqa: E402

app = FastAPI(
    title="天天半首诗 API",
    description="Daily Poetry Recitation - WeChat Mini Program Backend",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS 配置（开发环境，生产环境需收紧）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由（/api/v1）
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/")
async def root():
    return {
        "app": "天天半首诗 API",
        "version": "0.2.0",
        "docs": "/docs",
    }
