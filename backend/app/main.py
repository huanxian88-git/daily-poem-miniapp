from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="每日背诗 API",
    description="Daily Poetry Recitation - WeChat Mini Program Backend",
    version="0.1.0",
)

# CORS 配置（开发环境，生产环境需收紧）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# 后续阶段按需注册路由
# from app.api import auth, poems, recitation, review, profile
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
# app.include_router(poems.router, prefix="/api/v1/poems", tags=["诗词"])
# app.include_router(recitation.router, prefix="/api/v1/recite", tags=["背诵"])
# app.include_router(review.router, prefix="/api/v1/review", tags=["复习"])
# app.include_router(profile.router, prefix="/api/v1/profile", tags=["个人中心"])
