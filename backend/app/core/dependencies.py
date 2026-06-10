"""FastAPI 依赖注入函数。"""

from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.core.redis import get_redis as _get_redis
from app.core.security import decode_token
from app.schemas.common import (
    ERR_TOKEN_EXPIRED,
    ERR_TOKEN_INVALID,
    ERROR_MESSAGES,
    ResponseBase,
)


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）。"""
    async for session in _get_db():
        yield session


async def get_redis() -> Optional[aioredis.Redis]:
    """获取 Redis 连接（依赖注入）。"""
    return await _get_redis()


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> dict:
    """从 Authorization Header 中解析当前用户信息。

    Header 格式: "Bearer <access_token>"

    Returns:
        用户信息字典 {"sub": user_id, "openid": openid, ...}。

    Raises:
        HTTPException: Token 缺失、无效或过期。
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail=ResponseBase(
                code=ERR_TOKEN_INVALID,
                message="Missing authorization header",
            ).model_dump(),
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail=ResponseBase(
                code=ERR_TOKEN_INVALID,
                message="Invalid authorization header format",
            ).model_dump(),
        )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail=ResponseBase(
                    code=ERR_TOKEN_INVALID,
                    message=ERROR_MESSAGES[ERR_TOKEN_INVALID],
                ).model_dump(),
            )
        return payload
    except ValueError as exc:
        msg = str(exc)
        code = (
            ERR_TOKEN_EXPIRED
            if "expired" in msg.lower()
            else ERR_TOKEN_INVALID
        )
        raise HTTPException(
            status_code=401,
            detail=ResponseBase(
                code=code,
                message=msg,
            ).model_dump(),
        )
