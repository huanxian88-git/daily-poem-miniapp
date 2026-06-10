"""鉴权测试 —— 微信登录 / Token刷新 / 用户信息。"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token


# ---- 登录测试 ----


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """测试 POST /api/v1/auth/login（DEV_MODE 自动 mock）。"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_wx_code"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["accessToken"] is not None
    assert data["data"]["refreshToken"] is not None
    assert "user" in data["data"]
    assert "openid" in data["data"]["user"]


@pytest.mark.asyncio
async def test_login_missing_code(client: AsyncClient):
    """测试登录缺少 code 参数。"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"code": ""},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_wx_api_failure(client: AsyncClient):
    """测试微信 API 调用失败。

    在 DEV_MODE 下 mock auth_service 中的 wechat_code2session 引用，
    使其抛出异常，确保登录流程能正确传播错误。
    """
    with patch(
        "app.services.auth_service.wechat_code2session",
        side_effect=ValueError("Invalid WeChat login code"),
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={"code": "bad_code"},
        )
    assert response.status_code == 401


# ---- Token 刷新测试 ----


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """测试 POST /api/v1/auth/refresh。"""
    # 先登录获取 refreshToken（DEV_MODE mock）
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_refresh"},
    )

    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["data"]["refreshToken"]

    # 使用 refreshToken 刷新
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["accessToken"] is not None
    assert data["data"]["refreshToken"] is not None


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """测试使用无效 refreshToken。"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": "invalid_token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_empty_token(client: AsyncClient):
    """测试刷新请求传空 refreshToken。"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": ""},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_with_access_token(client: AsyncClient):
    """测试 accessToken 不能用于刷新（type=access 应被拒绝）。"""
    # 先登录创建用户
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_type_check"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["data"]["accessToken"]

    # 用 accessToken 去刷新——token type 不匹配
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": access_token},
    )
    assert response.status_code == 401


# ---- 用户信息测试 ----


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient):
    """测试 GET /api/v1/auth/me（带 token）。"""
    # 先登录创建用户
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_me"},
    )

    assert login_resp.status_code == 200
    access_token = login_resp.json()["data"]["accessToken"]

    # 使用 accessToken 获取用户信息
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["openid"] is not None


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    """测试 GET /api/v1/auth/me（不带 token）。"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """测试 GET /api/v1/auth/me（无效 token）。"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


# ---- 安全模块单元测试 ----


@pytest.mark.asyncio
async def test_security_decode_token():
    """测试 JWT 签发与解码。"""
    token = create_access_token({"sub": "test-user", "openid": "test_openid"})
    from app.core.security import decode_token

    payload = decode_token(token)
    assert payload["sub"] == "test-user"
    assert payload["openid"] == "test_openid"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_security_invalid_token():
    """测试解码无效 token 抛出异常。"""
    from app.core.security import decode_token

    with pytest.raises(ValueError):
        decode_token("invalid_token_here")
