"""画像模块单元测试 —— 覆盖 Profile CRUD 全部字段与边界条件。

共 13 条用例，涵盖：
- 鉴权守卫（401）
- 默认值验证
- 全字段 / 部分字段更新
- interests 序列化往返
- 课本绑定三字段
- is_student 布尔切换
- POST 创建幂等性
- 画像不存在极端路径（404）
"""

import pytest
from httpx import AsyncClient


# ---- 辅助 ----

async def _login(client: AsyncClient, code_suffix: str = "default") -> str:
    """快捷登录并返回 access_token。"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"code": f"test_profile_{code_suffix}"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---- 1. GET 画像（默认值验证）----


@pytest.mark.asyncio
async def test_profile_get_defaults(client: AsyncClient):
    """登录后自动创建画像，验证所有默认值。"""
    token = await _login(client, "defaults")
    resp = await client.get("/api/v1/profile", headers=_auth_header(token))
    assert resp.status_code == 200
    d = resp.json()

    # 未设置的应为 None
    assert d["age_group"] is None
    assert d["level"] is None
    assert d["interests"] == []
    assert d["textbook_version"] is None
    assert d["textbook_grade"] is None
    assert d["textbook_semester"] is None
    assert d["is_student"] is False

    # 有默认值的字段
    assert d["recite_rhythm"] == "every_2_days"
    assert d["recite_rhythm_custom_days"] is None


# ---- 2. GET 画像（未登录 → 401）----


@pytest.mark.asyncio
async def test_profile_get_unauthorized(client: AsyncClient):
    """未登录访问画像返回 401。"""
    resp = await client.get("/api/v1/profile")
    assert resp.status_code == 401


# ---- 3. GET 画像（用户无画像 → 404）----


@pytest.mark.asyncio
async def test_profile_get_not_found(client: AsyncClient):
    """登录后手动删除画像，GET 应返回 404。"""
    from app.core.database import async_session
    from app.models.user import UserProfile

    token = await _login(client, "no_profile")
    # 通过 DB 删除刚创建的画像
    async with async_session() as db:
        from sqlalchemy import select
        from app.core.security import decode_token
        payload = decode_token(token)
        user_id = payload["sub"]
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            await db.delete(profile)
            await db.commit()

    resp = await client.get("/api/v1/profile", headers=_auth_header(token))
    assert resp.status_code == 404


# ---- 4. PUT 画像（部分更新，未传字段保持不变）----


@pytest.mark.asyncio
async def test_profile_update_partial(client: AsyncClient):
    """仅更新 age_group，其他字段保持原值。"""
    token = await _login(client, "partial")

    # 先全量设置
    await client.put(
        "/api/v1/profile",
        json={
            "age_group": "teen",
            "level": "beginner",
            "interests": ["思乡", "山水"],
            "recite_rhythm": "daily",
            "is_student": True,
        },
        headers=_auth_header(token),
    )

    # 仅更新 age_group
    resp = await client.put(
        "/api/v1/profile",
        json={"age_group": "adult"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["age_group"] == "adult"
    # 其他字段不变
    assert d["level"] == "beginner"
    assert d["interests"] == ["思乡", "山水"]
    assert d["recite_rhythm"] == "daily"
    assert d["is_student"] is True


# ---- 5. PUT 画像（全字段更新）----


@pytest.mark.asyncio
async def test_profile_update_all_fields(client: AsyncClient):
    """一次性更新画像全部字段。"""
    token = await _login(client, "all_fields")

    resp = await client.put(
        "/api/v1/profile",
        json={
            "age_group": "teen",
            "level": "intermediate",
            "interests": ["思乡", "山水", "边塞"],
            "recite_rhythm": "custom",
            "recite_rhythm_custom_days": 3,
            "textbook_version": "人教版（统编版）",
            "textbook_grade": 7,
            "textbook_semester": "upper",
            "is_student": True,
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    d = resp.json()

    assert d["age_group"] == "teen"
    assert d["level"] == "intermediate"
    assert d["interests"] == ["思乡", "山水", "边塞"]
    assert d["recite_rhythm"] == "custom"
    assert d["recite_rhythm_custom_days"] == 3
    assert d["textbook_version"] == "人教版（统编版）"
    assert d["textbook_grade"] == 7
    assert d["textbook_semester"] == "upper"
    assert d["is_student"] is True


# ---- 6. PUT 画像（interests 空列表 → 清空）----


@pytest.mark.asyncio
async def test_profile_update_interests_empty(client: AsyncClient):
    """先设置 interests，再传空列表清空。"""
    token = await _login(client, "interests_empty")

    # 设置
    await client.put(
        "/api/v1/profile",
        json={"interests": ["思乡", "山水"]},
        headers=_auth_header(token),
    )

    # 清空
    resp = await client.put(
        "/api/v1/profile",
        json={"interests": []},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["interests"] == []


# ---- 7. PUT 画像（课本绑定三字段）----


@pytest.mark.asyncio
async def test_profile_update_textbook(client: AsyncClient):
    """单独更新课本绑定三字段。"""
    token = await _login(client, "textbook")

    resp = await client.put(
        "/api/v1/profile",
        json={
            "textbook_version": "人教版（统编版）",
            "textbook_grade": 8,
            "textbook_semester": "lower",
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["textbook_version"] == "人教版（统编版）"
    assert d["textbook_grade"] == 8
    assert d["textbook_semester"] == "lower"


# ---- 8. PUT 画像（is_student 布尔切换）----


@pytest.mark.asyncio
async def test_profile_update_is_student_toggle(client: AsyncClient):
    """is_student 默认 False → True → False 往返切换。"""
    token = await _login(client, "student_toggle")

    # 默认 False
    resp = await client.get("/api/v1/profile", headers=_auth_header(token))
    assert resp.json()["is_student"] is False

    # 切为 True
    resp = await client.put(
        "/api/v1/profile",
        json={"is_student": True},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["is_student"] is True

    # 切回 False
    resp = await client.put(
        "/api/v1/profile",
        json={"is_student": False},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["is_student"] is False


# ---- 9. PUT 画像（recite_rhythm_custom_days）----


@pytest.mark.asyncio
async def test_profile_update_custom_rhythm(client: AsyncClient):
    """设置自定义背诵节奏 + custom_days。"""
    token = await _login(client, "custom_rhythm")

    resp = await client.put(
        "/api/v1/profile",
        json={"recite_rhythm": "custom", "recite_rhythm_custom_days": 5},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["recite_rhythm"] == "custom"
    assert d["recite_rhythm_custom_days"] == 5


# ---- 10. POST 画像（创建幂等性：已有画像时返回现有）----


@pytest.mark.asyncio
async def test_profile_create_idempotent(client: AsyncClient):
    """POST /profile 画像已存在时返回现有记录而非报错。"""
    token = await _login(client, "create_idempotent")

    # 登录已自动创建画像，先读取
    get_resp = await client.get("/api/v1/profile", headers=_auth_header(token))
    assert get_resp.status_code == 200
    original = get_resp.json()

    # POST 再创建应返回同一条
    post_resp = await client.post("/api/v1/profile", headers=_auth_header(token))
    assert post_resp.status_code == 200
    after = post_resp.json()

    # 关键字段一致（说明是同一条记录）
    assert after["age_group"] == original["age_group"]
    assert after["level"] == original["level"]
    assert after["recite_rhythm"] == original["recite_rhythm"]


# ---- 11. interests 序列化往返（逗号存 → 列表出 → 逗号存 → 列表出）----


@pytest.mark.asyncio
async def test_profile_interests_serialization(client: AsyncClient):
    """验证 interests 在 DB 层逗号分隔、API 层列表的序列化往返。"""
    token = await _login(client, "interests_ser")

    # 设置含中文逗号的兴趣
    resp = await client.put(
        "/api/v1/profile",
        json={"interests": ["思乡", "山水", "边塞", "咏物"]},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["interests"] == ["思乡", "山水", "边塞", "咏物"]

    # 修改为部分重叠
    resp = await client.put(
        "/api/v1/profile",
        json={"interests": ["思乡", "田园"]},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["interests"] == ["思乡", "田园"]


# ---- 12. PUT 画像（无 token → 401）----


@pytest.mark.asyncio
async def test_profile_update_unauthorized(client: AsyncClient):
    """未登录 PUT 画像返回 401。"""
    resp = await client.put(
        "/api/v1/profile",
        json={"age_group": "adult"},
    )
    assert resp.status_code == 401


# ---- 13. PUT 画像后 GET 读取验证持久性 ----


@pytest.mark.asyncio
async def test_profile_update_then_get(client: AsyncClient):
    """PUT 更新后再 GET，验证数据持久化。"""
    token = await _login(client, "persist")

    # 更新
    await client.put(
        "/api/v1/profile",
        json={
            "age_group": "child",
            "level": "beginner",
            "interests": ["童趣"],
            "recite_rhythm": "daily",
            "textbook_grade": 7,
            "is_student": True,
        },
        headers=_auth_header(token),
    )

    # 重新读取
    resp = await client.get("/api/v1/profile", headers=_auth_header(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["age_group"] == "child"
    assert d["level"] == "beginner"
    assert d["interests"] == ["童趣"]
    assert d["recite_rhythm"] == "daily"
    assert d["textbook_grade"] == 7
    assert d["is_student"] is True
