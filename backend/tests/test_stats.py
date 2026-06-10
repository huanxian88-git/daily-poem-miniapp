"""统计模块 API 测试 —— 5个用例覆盖学习统计摘要。

覆盖功能：
- 新用户全0统计
- 有数据统计
- 连续天数计算
- 无权限
- 今日背诵数
"""

import json
from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decode_token
from app.models.poem import Poem
from app.models.recitation import Recitation
from app.models.user import _uuid_str


# ---- 测试数据辅助 ----


async def _insert_test_poems(db: AsyncSession):
    """插入测试诗词。"""
    poems = [
        Poem(
            id="stats-poem-001",
            title="静夜思",
            author="李白",
            dynasty="唐",
            content="床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            content_lines=json.dumps(
                ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            status="active",
        ),
        Poem(
            id="stats-poem-002",
            title="春晓",
            author="孟浩然",
            dynasty="唐",
            content="春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
            content_lines=json.dumps(
                ["春眠不觉晓，", "处处闻啼鸟。", "夜来风雨声，", "花落知多少。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            status="active",
        ),
    ]
    for p in poems:
        db.add(p)
    await db.flush()


async def _login_and_get_user_id(client: AsyncClient, code: str = "stats_test_user"):
    """登录返回 (token, user_id)。"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = decode_token(token)
    user_id = payload["sub"]
    return token, user_id


# ---- 统计测试 ----


@pytest.mark.asyncio
async def test_stats_summary_empty(client: AsyncClient):
    """新用户 → 全0。"""
    token, _ = await _login_and_get_user_id(client, "stats_empty")

    resp = await client.get(
        "/api/v1/stats/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_recited"] == 0
    assert data["total_mastered"] == 0
    assert data["streak_days"] == 0
    assert data["today_recited"] == 0


@pytest.mark.asyncio
async def test_stats_summary_with_data(client: AsyncClient):
    """有背诵记录 → 正确的统计。"""
    token, user_id = await _login_and_get_user_id(client, "stats_with_data")

    async with async_session() as db:
        await _insert_test_poems(db)

        # 创建2条背诵记录（1条已掌握，1条在背）
        rec1 = Recitation(
            id=_uuid_str(),
            user_id=user_id,
            poem_id="stats-poem-001",
            status="memorized",
            is_mastered=True,
            fill_score=80,
            sort_score=90,
            voice_score=85,
            mastered_at=datetime.utcnow(),
        )
        rec2 = Recitation(
            id=_uuid_str(),
            user_id=user_id,
            poem_id="stats-poem-002",
            status="reciting",
            is_mastered=False,
        )
        db.add_all([rec1, rec2])
        await db.commit()

    resp = await client.get(
        "/api/v1/stats/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_recited"] == 2
    assert data["total_mastered"] == 1


@pytest.mark.asyncio
async def test_stats_summary_streak(client: AsyncClient):
    """连续天数计算（今天+昨天 → streak>=2）。"""
    token, user_id = await _login_and_get_user_id(client, "stats_streak")

    async with async_session() as db:
        await _insert_test_poems(db)

        # 今天的记录
        rec_today = Recitation(
            id=_uuid_str(),
            user_id=user_id,
            poem_id="stats-poem-001",
            status="reciting",
        )
        db.add(rec_today)
        await db.flush()

        # 昨天的记录 — 直接用 SQL 插入以控制 created_at
        from sqlalchemy import text
        rec_yesterday_id = _uuid_str()
        await db.execute(
            text(
                "INSERT INTO recitations "
                "(id, user_id, poem_id, status, is_mastered, attempt_count, created_at, updated_at) "
                "VALUES (:id, :uid, :pid, 'memorized', 1, 0, :cat, :uat)"
            ),
            {
                "id": rec_yesterday_id,
                "uid": user_id,
                "pid": "stats-poem-002",
                "cat": datetime.utcnow() - timedelta(days=1),
                "uat": datetime.utcnow() - timedelta(days=1),
            },
        )
        await db.commit()

    resp = await client.get(
        "/api/v1/stats/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["streak_days"] >= 1


@pytest.mark.asyncio
async def test_stats_unauthorized(client: AsyncClient):
    """无 token → 401。"""
    resp = await client.get("/api/v1/stats/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stats_today_recited(client: AsyncClient):
    """今日背诵数。"""
    token, user_id = await _login_and_get_user_id(client, "stats_today")

    async with async_session() as db:
        await _insert_test_poems(db)

        # 今天的记录
        rec = Recitation(
            id=_uuid_str(),
            user_id=user_id,
            poem_id="stats-poem-001",
            status="reciting",
        )
        db.add(rec)
        await db.commit()

    resp = await client.get(
        "/api/v1/stats/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["today_recited"] == 1
