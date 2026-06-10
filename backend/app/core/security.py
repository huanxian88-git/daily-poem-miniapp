"""安全模块：JWT 签发/验证 + 微信 code2session"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from jose import JWTError, jwt

from app.core.config import settings

# JWT 配置
ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET
TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


# --- JWT ---

def create_access_token(user_id: str, openid: str) -> str:
    """签发 JWT Access Token"""
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "openid": openid,
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """签发 Refresh Token"""
    expire = datetime.utcnow() + timedelta(days=30)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT 并返回 payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# 别名，供 dependencies.py 使用
decode_token = verify_token


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """用 Refresh Token 刷新 Access Token"""
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    openid = payload.get("openid", "")
    if not user_id:
        return None
    return create_access_token(user_id, openid)


# --- 微信 code2session ---

async def wx_code2session(code: str) -> Optional[dict]:
    """用微信登录 code 换取 openid + session_key

    DEV_MODE 下返回 mock 数据，无需真实微信 API。
    """
    if settings.DEV_MODE:
        # 开发模式：用 code 的 hash 生成确定性 openid
        mock_openid = f"dev_{hash(code) % 1000000:06d}"
        return {
            "openid": mock_openid,
            "session_key": "mock_session_key",
            "unionid": None,
        }

    url = settings.WECHAT_CODE2SESSION_URL
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "errcode" in data and data["errcode"] != 0:
        return None  # 微信返回错误

    return {
        "openid": data.get("openid"),
        "session_key": data.get("session_key"),
        "unionid": data.get("unionid"),
    }
