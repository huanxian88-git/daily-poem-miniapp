"""API 路由注册中心"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.poems import router as poems_router
from app.api.v1.daily import router as daily_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.recitation import router as recitation_router
from app.api.v1.review import router as review_router
from app.api.v1.stats import router as stats_router

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(profile_router, prefix="/profile", tags=["用户画像"])
api_router.include_router(poems_router, prefix="/poems", tags=["诗词"])
api_router.include_router(daily_router, prefix="/daily", tags=["每日推荐"])
api_router.include_router(favorites_router, prefix="/favorites", tags=["珍藏"])
api_router.include_router(recitation_router, prefix="/recite", tags=["背诵"])
api_router.include_router(review_router, prefix="/review", tags=["复习"])
api_router.include_router(stats_router, prefix="/stats", tags=["统计"])
