"""应用配置管理 —— Pydantic Settings。"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---- 应用 ----
    APP_NAME: str = "天天半首诗 API"
    DEBUG: bool = False
    DEV_MODE: bool = False

    # ---- 数据库 ----
    # 开发环境：sqlite+aiosqlite:///./data/daily_poem.db
    # 生产环境：postgresql+asyncpg://user:pass@host:5432/daily_poem
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/daily_poem.db"

    # ---- Redis ----
    # 开发环境可留空跳过Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    # 是否允许Redis不可用时降级
    REDIS_GRACEFUL_DEGRADATION: bool = True

    # ---- 微信小程序 ----
    WECHAT_APPID: str = "wxcb715f5de1dee100"
    WECHAT_SECRET: str = ""
    WECHAT_CODE2SESSION_URL: str = (
        "https://api.weixin.qq.com/sns/jscode2session"
    )

    # ---- JWT ----
    JWT_SECRET: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30天

    # ---- 腾讯混元 ----
    HUNYUAN_API_KEY: str = ""
    HUNYUAN_API_URL: str = "https://hunyuan.tencentcloudapi.com"
    HUNYUAN_MODEL: str = "hunyuan-lite"

    # ---- 腾讯云 ASR ----
    TENCENT_SECRET_ID: str = ""
    TENCENT_SECRET_KEY: str = ""
    TENCENT_ASR_REGION: str = "ap-guangzhou"
    TENCENT_APPID: str = ""

    # ---- 腾讯云 COS ----
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_REGION: str = "ap-guangzhou"
    COS_BUCKET: str = ""

    # ---- CORS ----
    CORS_ORIGINS: List[str] = ["*"]

    @property
    def is_development(self) -> bool:
        return self.DEV_MODE or self.DEBUG

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
