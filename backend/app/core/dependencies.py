"""FastAPI 依赖注入函数。"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.core.security import verify_token
from app.schemas.common import ERR_TOKEN_INVALID, ERR_TOKEN_EXPIRED


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）。"""
    async for session in _get_db():
        yield session


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    """从 Authorization Header 中解析当前用户信息。

    Header 格式: "Bearer <access_token>"

    Returns:
        用户信息字典 {"sub": user_id, "openid": openid, ...}
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
        )

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token 无效或已过期",
        )

    # 只允许 access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="需要 access token",
        )

    return payload
