from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.redis import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 Redis，关闭时释放"""
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="每日背诗 API",
    description="Daily Poetry Recitation - WeChat Mini Program Backend",
    version="0.1.0",
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
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {
        "app": "每日背诗 API",
        "version": "0.1.0",
        "docs": "/docs",
    }
