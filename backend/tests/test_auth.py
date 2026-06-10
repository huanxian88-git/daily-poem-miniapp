"""阶段2 API 测试 —— 鉴权/画像/诗词/每日/珍藏。

所有测试使用内存 SQLite，通过 login 创建用户 + 画像，
通过 seed fixture 插入测试诗词数据。
"""

import json
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.database import async_session
from app.models.poem import Poem
from app.models.event import Festival
from app.models.recommendation import DailyRecommendation
from app.models.textbook import Textbook, PoemTextbook


# ---- 种子数据 fixture ----


@pytest.mark.asyncio
async def _insert_test_poems(db: AsyncSession):
    """插入测试用诗词数据（3首）。"""
    poems = [
        Poem(
            id="test-poem-001",
            title="静夜思",
            author="李白",
            dynasty="唐",
            content="床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            content_lines=json.dumps(
                ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            tags="意象:月|主题:思乡|场景:秋夜",
            scene_type="月夜",
            scene_desc="秋夜静谧，明月高悬，游子独坐窗前，银辉洒地如霜。",
        ),
        Poem(
            id="test-poem-002",
            title="春晓",
            author="孟浩然",
            dynasty="唐",
            content="春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
            content_lines=json.dumps(
                ["春眠不觉晓，", "处处闻啼鸟。", "夜来风雨声，", "花落知多少。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            tags="意象:鸟,意象:花|主题:惜春|场景:清晨",
            scene_type="春晨",
            scene_desc="春日清晨，鸟鸣声声，昨夜风雨过后，花瓣洒满庭院。",
        ),
        Poem(
            id="test-poem-003",
            title="登鹳雀楼",
            author="王之涣",
            dynasty="唐",
            content="白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
            difficulty=1,
            tags="意象:白日,意象:黄河|主题:登高|场景:黄昏",
            scene_type="黄昏",
            scene_desc="落日余晖映群山，黄河滚滚东入海，登高望远心胸开。",
        ),
        Poem(
            id="test-poem-004",
            title="悯农",
            author="李绅",
            dynasty="唐",
            content="锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。",
            difficulty=1,
            tags="意象:烈日,意象:禾|主题:悯农|场景:农田",
        ),
        Poem(
            id="test-poem-005",
            title="咏鹅",
            author="骆宾王",
            dynasty="唐",
            content="鹅鹅鹅，曲项向天歌。白毛浮绿水，红掌拨清波。",
            difficulty=1,
            tags="意象:鹅,意象:绿水|主题:咏物|场景:水边",
        ),
    ]
    for p in poems:
        db.add(p)
    await db.flush()


@pytest.mark.asyncio
async def _insert_test_daily(db: AsyncSession):
    """插入今日推荐数据。"""
    recs = [
        DailyRecommendation(
            id="test-daily-001",
            poem_id="test-poem-001",
            recommend_date=date.today(),
            reason="经典咏流传，李白望月思故乡",
            reason_type="manual",
            is_pinned=True,
        ),
        DailyRecommendation(
            id="test-daily-002",
            poem_id="test-poem-002",
            recommend_date=date.today(),
            reason="春意盎然，惜春好诗",
            reason_type="manual",
        ),
        DailyRecommendation(
            id="test-daily-003",
            poem_id="test-poem-003",
            recommend_date=date.today(),
            reason="登高望远，心胸开阔",
            reason_type="manual",
        ),
    ]
    for r in recs:
        db.add(r)
    await db.flush()


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
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data
    assert "is_new_user" in data


@pytest.mark.asyncio
async def test_login_missing_code(client: AsyncClient):
    """测试登录缺少 code 参数 -> 422。"""
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_wx_api_failure(client: AsyncClient):
    """测试微信 API 调用失败。"""
    with patch(
        "app.api.v1.auth.wx_code2session",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={"code": "bad_code"},
        )
    assert response.status_code == 400


# ---- Token 刷新测试 ----


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """测试 POST /api/v1/auth/refresh。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_refresh"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """测试使用无效 refresh_token -> 401。"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token_string"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_empty_token(client: AsyncClient):
    """测试刷新请求传空 refresh_token。"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ""},
    )
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_refresh_with_access_token(client: AsyncClient):
    """测试 access_token 不能用于刷新。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_type_check"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401


# ---- 用户信息测试 ----


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient):
    """测试 GET /api/v1/auth/me（带 token）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_me"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    """测试 GET /api/v1/auth/me（不带 token）-> 401。"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """测试 GET /api/v1/auth/me（无效 token）-> 401。"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


# ---- 安全模块单元测试 ----


@pytest.mark.asyncio
async def test_security_decode_token():
    """测试 JWT 签发与解码。"""
    token = create_access_token("test-user-id", "test_openid")
    payload = decode_token(token)
    assert payload["sub"] == "test-user-id"
    assert payload["openid"] == "test_openid"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_security_invalid_token():
    """测试解码无效 token 返回 None。"""
    result = decode_token("invalid_token_here")
    assert result is None


# ---- 画像 API 测试（阶段2：真实 DB）----


@pytest.mark.asyncio
async def test_profile_get(client: AsyncClient):
    """测试 GET /api/v1/profile（登录后自动创建画像）。"""
    # 登录创建用户 + 画像
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_profile_get"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "age_group" in data
    assert "interests" in data
    assert "recite_rhythm" in data


@pytest.mark.asyncio
async def test_profile_update(client: AsyncClient):
    """测试 PUT /api/v1/profile（更新画像）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_profile_update"},
    )
    token = login_resp.json()["access_token"]

    response = await client.put(
        "/api/v1/profile",
        json={"age_group": "adult", "level": "beginner", "interests": ["思乡", "山水"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["age_group"] == "adult"
    assert data["level"] == "beginner"
    assert data["interests"] == ["思乡", "山水"]


# ---- 诗词 API 测试（阶段2）----


@pytest.mark.asyncio
async def test_poems_list(client: AsyncClient):
    """测试 GET /api/v1/poems（列表，需要种子数据）。"""
    # 登录
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_poems_list"},
    )
    token = login_resp.json()["access_token"]

    # 先插入测试诗词
    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    response = await client.get(
        "/api/v1/poems?page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert len(data["poems"]) >= 5


@pytest.mark.asyncio
async def test_poem_detail(client: AsyncClient):
    """测试 GET /api/v1/poems/{id}（诗词详情）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_poem_detail"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    response = await client.get(
        "/api/v1/poems/test-poem-001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "静夜思"
    assert data["author"] == "李白"
    assert data["content"] != ""
    assert "is_favorited" in data


@pytest.mark.asyncio
async def test_poem_scene(client: AsyncClient):
    """测试 GET /api/v1/poems/{id}/scene（诗词场景）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_poem_scene"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    response = await client.get(
        "/api/v1/poems/test-poem-001/scene",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "scene_type" in data
    assert "scene_desc" in data


# ---- 每日推荐 API 测试（阶段2）----


@pytest.mark.asyncio
async def test_daily_today(client: AsyncClient):
    """测试 GET /api/v1/daily/today。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_daily_today"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await _insert_test_daily(db)
        await db.commit()

    response = await client.get(
        "/api/v1/daily/today",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["poem"]["title"] == "静夜思"
    assert data["reason"] != ""
    assert "can_switch" in data


@pytest.mark.asyncio
async def test_daily_switch(client: AsyncClient):
    """测试 POST /api/v1/daily/switch（换一首）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_daily_switch"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await _insert_test_daily(db)
        await db.commit()

    response = await client.post(
        "/api/v1/daily/switch",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["poem"]["title"] in ["春晓", "登鹳雀楼", "悯农", "咏鹅"]  # 轮换到一首新诗
    assert data["switch_count"] >= 1


# ---- 珍藏 API 测试（阶段2：POST/DELETE/GET）----


@pytest.mark.asyncio
async def test_favorite_add_and_list(client: AsyncClient):
    """测试 POST /favorites/{id} 添加珍藏 + GET /favorites 列表。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_fav_add"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    # 添加珍藏
    response = await client.post(
        "/api/v1/favorites/test-poem-001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorited"] is True

    # 查看珍藏列表
    response = await client.get(
        "/api/v1/favorites",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_favorite_remove(client: AsyncClient):
    """测试 DELETE /favorites/{id} 取消珍藏。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_fav_remove"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    # 先添加
    await client.post(
        "/api/v1/favorites/test-poem-002",
        headers={"Authorization": f"Bearer {token}"},
    )
    # 再删除
    response = await client.delete(
        "/api/v1/favorites/test-poem-002",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_favorited"] is False


# ---- 诗词搜索与筛选测试 ----


@pytest.mark.asyncio
async def test_poems_search(client: AsyncClient):
    """测试 GET /api/v1/poems?search=李白（搜索）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_poems_search"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    response = await client.get(
        "/api/v1/poems?search=李白",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["poems"][0]["author"] == "李白"


@pytest.mark.asyncio
async def test_poems_filter_difficulty(client: AsyncClient):
    """测试 GET /api/v1/poems?difficulty=1（难度筛选）。"""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"code": "test_code_poems_filter"},
    )
    token = login_resp.json()["access_token"]

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    response = await client.get(
        "/api/v1/poems?difficulty=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3  # 3首难度1的诗
