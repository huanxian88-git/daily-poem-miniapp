"""API 路由注册中心"""

from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 后续阶段按需注册
# api_router.include_router(poems.router, prefix="/poems", tags=["诗词"])
# api_router.include_router(daily.router, prefix="/daily", tags=["每日推荐"])
# api_router.include_router(recite.router, prefix="/recite", tags=["背诵"])
# api_router.include_router(review.router, prefix="/review", tags=["复习"])
# api_router.include_router(profile.router, prefix="/profile", tags=["个人中心"])
# api_router.include_router(favorites.router, prefix="/favorites", tags=["珍藏"])
