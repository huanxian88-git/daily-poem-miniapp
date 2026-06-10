"""认证 API：微信登录 / Token刷新"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    refresh_access_token,
    wx_code2session,
)
from app.models.user import User, UserProfile

router = APIRouter()


# --- Request/Response Schemas ---

class LoginRequest(BaseModel):
    code: str  # 微信 wx.login() 返回的 code


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int  # token 有效期（秒）
    is_new_user: bool


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


# --- API 端点 ---

@router.post("/login", response_model=TokenResponse)
async def wx_login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """微信登录：code 换 token"""
    # 1. 调用微信 code2session
    wx_data = await wx_code2session(req.code)
    if not wx_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败，请检查 code 是否有效",
        )

    openid = wx_data["openid"]

    # 2. 查找或创建用户
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    is_new_user = False
    if not user:
        is_new_user = True
        user = User(
            id=uuid.uuid4(),
            openid=openid,
            unionid=wx_data.get("unionid"),
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        await db.flush()

        # 为新用户创建空白画像
        profile = UserProfile(
            id=uuid.uuid4(),
            user_id=user.id,
        )
        db.add(profile)
    else:
        user.last_login_at = datetime.utcnow()

    await db.commit()

    # 3. 签发双 Token
    user_id_str = str(user.id)
    access_token = create_access_token(user_id_str, openid)
    refresh_token = create_refresh_token(user_id_str)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=7 * 24 * 3600,
        is_new_user=is_new_user,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(req: RefreshRequest):
    """刷新 Access Token"""
    new_token = refresh_access_token(req.refresh_token)
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期",
        )

    return RefreshResponse(
        access_token=new_token,
        expires_in=7 * 24 * 3600,
    )
