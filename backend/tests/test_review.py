"""复习模块 API 测试 —— 10个用例覆盖复习调度全流程。

覆盖功能：
- 复习队列（空队列/有到期/排序/无权限）
- 标记复习完成（easy/good/hard/next_date更新/不存在）
- 复习统计
"""

import json
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decode_token
from app.models.poem import Poem
from app.models.recitation import Recitation
from app.models.review import ReviewSchedule
from app.models.user import _uuid_str


# ---- 测试数据辅助 ----


async def _insert_test_poems(db: AsyncSession):
    """插入3首测试诗词。"""
    poems = [
        Poem(
            id="review-poem-001",
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
            id="review-poem-002",
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
        Poem(
            id="review-poem-003",
            title="登鹳雀楼",
            author="王之涣",
            dynasty="唐",
            content="白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
            content_lines=json.dumps(
                ["白日依山尽，", "黄河入海流。", "欲穷千里目，", "更上一层楼。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            status="active",
        ),
    ]
    for p in poems:
        db.add(p)
    await db.flush()


async def _create_review_schedule(
    db: AsyncSession,
    user_id: str,
    poem_id: str,
    next_review_date: date,
    ease_factor: float = 2.5,
    interval_days: int = 1,
    review_count: int = 0,
) -> ReviewSchedule:
    """创建复习计划。"""
    schedule = ReviewSchedule(
        id=_uuid_str(),
        user_id=user_id,
        poem_id=poem_id,
        next_review_date=next_review_date,
        ease_factor=ease_factor,
        interval_days=interval_days,
        review_count=review_count,
    )
    db.add(schedule)
    await db.flush()
    return schedule


async def _login_and_get_user_id(client: AsyncClient, code: str = "review_test_user"):
    """登录并返回 (token, user_id)。"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = decode_token(token)
    user_id = payload["sub"]
    return token, user_id


# ---- 复习队列 ----


@pytest.mark.asyncio
async def test_review_queue_empty(client: AsyncClient):
    """无复习项 → 空列表。"""
    token, user_id = await _login_and_get_user_id(client, "review_queue_empty")

    resp = await client.get(
        "/api/v1/review/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_review_queue_with_items(client: AsyncClient):
    """有到期复习 → 返回队列。"""
    token, user_id = await _login_and_get_user_id(client, "review_queue_items")

    async with async_session() as db:
        await _insert_test_poems(db)
        # 创建今日到期的复习计划
        await _create_review_schedule(
            db, user_id, "review-poem-001", date.today(),
        )
        await db.commit()

    resp = await client.get(
        "/api/v1/review/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["poem_title"] == "静夜思"


@pytest.mark.asyncio
async def test_review_queue_ordering(client: AsyncClient):
    """紧急的排在前面（8天前到期的=high 排在 1天前到期的=low 前面）。"""
    token, user_id = await _login_and_get_user_id(client, "review_queue_order")

    async with async_session() as db:
        await _insert_test_poems(db)
        # 8天前到期 → urgency=high
        await _create_review_schedule(
            db, user_id, "review-poem-001",
            date.today() - timedelta(days=8),
        )
        # 1天前到期 → urgency=low
        await _create_review_schedule(
            db, user_id, "review-poem-002",
            date.today() - timedelta(days=1),
        )
        await db.commit()

    resp = await client.get(
        "/api/v1/review/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    # 8天前到期的应排在前面（next_review_date升序，越早越紧急）
    assert data["items"][0]["urgency"] == "high"
    assert data["items"][1]["urgency"] == "low"


@pytest.mark.asyncio
async def test_review_queue_unauthorized(client: AsyncClient):
    """无 token → 401。"""
    resp = await client.get("/api/v1/review/queue")
    assert resp.status_code == 401


# ---- 标记复习完成 ----


@pytest.mark.asyncio
async def test_review_done_easy(client: AsyncClient):
    """self_assessment=easy → 间隔增大。"""
    token, user_id = await _login_and_get_user_id(client, "review_done_easy")

    async with async_session() as db:
        await _insert_test_poems(db)
        await _create_review_schedule(
            db, user_id, "review-poem-001", date.today(),
            ease_factor=2.5, interval_days=1,
        )
        await db.commit()

    resp = await client.post(
        "/api/v1/review/review-poem-001/done",
        json={"self_assessment": "easy"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # easy: ease=2.5+0.15=2.65, interval=int(1*2.65)=2
    assert data["interval_days"] >= 2


@pytest.mark.asyncio
async def test_review_done_good(client: AsyncClient):
    """self_assessment=good → 正常间隔。"""
    token, user_id = await _login_and_get_user_id(client, "review_done_good")

    async with async_session() as db:
        await _insert_test_poems(db)
        await _create_review_schedule(
            db, user_id, "review-poem-001", date.today(),
            ease_factor=2.5, interval_days=1,
        )
        await db.commit()

    resp = await client.post(
        "/api/v1/review/review-poem-001/done",
        json={"self_assessment": "good"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # good: interval=int(1*2.5)=2
    assert data["interval_days"] == 2


@pytest.mark.asyncio
async def test_review_done_hard(client: AsyncClient):
    """self_assessment=hard → 间隔缩短 + ease_factor 降低。"""
    token, user_id = await _login_and_get_user_id(client, "review_done_hard")

    async with async_session() as db:
        await _insert_test_poems(db)
        await _create_review_schedule(
            db, user_id, "review-poem-001", date.today(),
            ease_factor=2.5, interval_days=3,
        )
        await db.commit()

    resp = await client.post(
        "/api/v1/review/review-poem-001/done",
        json={"self_assessment": "hard"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # hard: interval=max(1, int(3*0.6))=1
    assert data["interval_days"] == 1


@pytest.mark.asyncio
async def test_review_done_creates_next_date(client: AsyncClient):
    """复习后 next_review_date 正确更新。"""
    token, user_id = await _login_and_get_user_id(client, "review_done_date")

    async with async_session() as db:
        await _insert_test_poems(db)
        await _create_review_schedule(
            db, user_id, "review-poem-001", date.today(),
            ease_factor=2.5, interval_days=1,
        )
        await db.commit()

    resp = await client.post(
        "/api/v1/review/review-poem-001/done",
        json={"self_assessment": "good"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # good: interval=2, next_review_date = today + 2
    expected_date = date.today() + timedelta(days=2)
    assert data["next_review_date"] == expected_date.isoformat()


@pytest.mark.asyncio
async def test_review_done_not_found(client: AsyncClient):
    """poem_id 不存在 → 400。"""
    token, user_id = await _login_and_get_user_id(client, "review_done_404")

    resp = await client.post(
        "/api/v1/review/nonexistent-poem/done",
        json={"self_assessment": "good"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ---- 复习统计 ----


@pytest.mark.asyncio
async def test_review_stats(client: AsyncClient):
    """返回正确的统计数据。"""
    token, user_id = await _login_and_get_user_id(client, "review_stats")

    async with async_session() as db:
        await _insert_test_poems(db)
        # 创建2个复习计划（1个今日到期，1个未来）
        await _create_review_schedule(
            db, user_id, "review-poem-001", date.today(),
        )
        await _create_review_schedule(
            db, user_id, "review-poem-002", date.today() + timedelta(days=5),
        )
        await db.commit()

    resp = await client.get(
        "/api/v1/review/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["today_due"] == 1
    assert data["reviewing"] == 2
