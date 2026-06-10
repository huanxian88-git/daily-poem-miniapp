"""认证服务：微信登录 + JWT 管理。"""

import logging
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    wechat_code2session,
)
from app.models.user import User
from app.schemas.common import (
    ERR_INVALID_CODE,
    ERR_REFRESH_TOKEN_EXPIRED,
    ERR_REFRESH_TOKEN_INVALID,
    ERR_WECHAT_API_FAILED,
    ERROR_MESSAGES,
)

logger = logging.getLogger(__name__)


async def login(
    db: AsyncSession,
    code: str,
) -> Dict:
    """微信登录完整流程。

    1. code2session 获取 openid / session_key
    2. 查找或创建用户
    3. 签发 access_token + refresh_token

    Args:
        db: 数据库会话。
        code: 微信登录凭证。

    Returns:
        {
            "accessToken": str,
            "refreshToken": str,
            "expiresIn": int,
            "user": {"id", "openid", "nickname", "avatarUrl"}
        }

    Raises:
        ValueError: 登录失败。
    """
    # Step 1: code2session
    try:
        wx_session = await wechat_code2session(code)
    except ValueError:
        raise ValueError(ERROR_MESSAGES[ERR_INVALID_CODE])

    openid = wx_session["openid"]
    session_key = wx_session.get("session_key", "")
    unionid = wx_session.get("unionid")

    # Step 2: 查找或创建用户
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            openid=openid,
            unionid=unionid,
            session_key=session_key,
        )
        db.add(user)
        await db.flush()
        logger.info("New user created: openid=%s", openid[:12])
    else:
        # 更新 session_key 和 unionid（可能变化）
        user.session_key = session_key
        if unionid and not user.unionid:
            user.unionid = unionid
        logger.info("Existing user login: user_id=%s", user.id)

    # Step 3: 签发 JWT
    token_data = {
        "sub": str(user.id),
        "openid": openid,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": 60 * 24 * 7,  # 秒
        "user": {
            "id": str(user.id),
            "openid": user.openid,
            "nickname": user.nickname,
            "avatarUrl": user.avatar_url,
        },
    }


async def refresh_token(
    db: AsyncSession,
    refresh_token_str: str,
) -> Dict:
    """刷新 Access Token。

    验证 refresh token 有效性，返回新的 token 对。

    Args:
        db: 数据库会话。
        refresh_token_str: Refresh token 字符串。

    Returns:
        {
            "accessToken": str,
            "refreshToken": str,
            "expiresIn": int,
        }

    Raises:
        ValueError: Token 无效或过期。
    """
    # 验证 refresh token
    try:
        payload = decode_token(refresh_token_str)
    except ValueError:
        raise ValueError(ERROR_MESSAGES[ERR_REFRESH_TOKEN_INVALID])

    if payload.get("type") != "refresh":
        raise ValueError(ERROR_MESSAGES[ERR_REFRESH_TOKEN_INVALID])

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError(ERROR_MESSAGES[ERR_REFRESH_TOKEN_INVALID])

    # 确认用户存在
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError(ERROR_MESSAGES[ERR_REFRESH_TOKEN_INVALID])

    # 签发新的 token 对
    token_data = {
        "sub": str(user.id),
        "openid": user.openid,
    }
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return {
        "accessToken": access_token,
        "refreshToken": new_refresh_token,
        "expiresIn": 60 * 24 * 7,
    }


async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> Optional[User]:
    """通过用户 ID 查询用户。"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
