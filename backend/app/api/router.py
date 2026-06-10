"""API 路由汇总。"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.daily import router as daily_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.profile import router as profile_router

api_router = APIRouter()

# 注册各模块路由（prefix 仅负责分组，外层 main.py 统一加 /api/v1）
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(daily_router, prefix="/daily", tags=["每日推荐"])
api_router.include_router(favorites_router, prefix="/favorites", tags=["珍藏"])
api_router.include_router(profile_router, prefix="/profile", tags=["用户画像"])
