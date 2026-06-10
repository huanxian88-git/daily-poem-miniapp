from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "每日背诗 API"
    DEBUG: bool = False

    # 数据库（腾讯云 TDSQL-C PostgreSQL）
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/daily_poem"

    # Redis（腾讯云 Redis）
    REDIS_URL: str = "redis://localhost:6379/0"

    # 微信小程序
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    WECHAT_COD_E2SESSION_URL: str = "https://api.weixin.qq.com/sns/jscode2session"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 腾讯混元
    HUNYUAN_API_KEY: str = ""
    HUNYUAN_API_URL: str = "https://hunyuan.tencentcloudapi.com"

    # 腾讯云 ASR
    TENCENT_SECRET_ID: str = ""
    TENCENT_SECRET_KEY: str = ""
    TENCENT_ASR_REGION: str = "ap-guangzhou"

    # 腾讯云 COS
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_REGION: str = "ap-guangzhou"
    COS_BUCKET: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
