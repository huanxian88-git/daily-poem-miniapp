"""每日推荐升级测试（阶段3）—— 5个用例。

覆盖功能：
- 历史推荐分页
- 分页参数生效
- 今日推荐使用推荐引擎
- 换一首限制生效
- 无历史 → 空列表
"""

import json
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.poem import Poem
from app.models.recommendation import DailyRecommendation


# ---- 测试数据辅助 ----


async def _insert_test_poems(db: AsyncSession):
    """插入6首测试诗词（覆盖今日推荐 + 历史推荐 + 换一首）。"""
    poems = [
        Poem(
            id="daily-v2-poem-001",
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
            status="active",
        ),
        Poem(
            id="daily-v2-poem-002",
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
            status="active",
        ),
        Poem(
            id="daily-v2-poem-003",
            title="登鹳雀楼",
            author="王之涣",
            dynasty="唐",
            content="白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
            content_lines=json.dumps(
                ["白日依山尽，", "黄河入海流。", "欲穷千里目，", "更上一层楼。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            tags="意象:白日,意象:黄河|主题:登高|场景:黄昏",
            status="active",
        ),
        Poem(
            id="daily-v2-poem-004",
            title="悯农",
            author="李绅",
            dynasty="唐",
            content="锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。",
            difficulty=1,
            tags="意象:烈日|主题:悯农|场景:农田",
            status="active",
        ),
        Poem(
            id="daily-v2-poem-005",
            title="咏鹅",
            author="骆宾王",
            dynasty="唐",
            content="鹅鹅鹅，曲项向天歌。白毛浮绿水，红掌拨清波。",
            difficulty=1,
            tags="意象:鹅|主题:咏物|场景:水边",
            status="active",
        ),
        Poem(
            id="daily-v2-poem-006",
            title="江雪",
            author="柳宗元",
            dynasty="唐",
            content="千山鸟飞绝，万径人踪灭。孤舟蓑笠翁，独钓寒江雪。",
            difficulty=2,
            tags="意象:雪|主题:孤独|场景:雪景",
            status="active",
        ),
    ]
    for p in poems:
        db.add(p)
    await db.flush()


async def _login_and_get_token(client: AsyncClient, code: str = "daily_v2_user") -> str:
    """登录返回 token。"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ---- 测试用例 ----


@pytest.mark.asyncio
async def test_daily_history(client: AsyncClient):
    """历史推荐分页。"""
    token = await _login_and_get_token(client, "daily_v2_history")

    async with async_session() as db:
        await _insert_test_poems(db)
        # 插入3条历史推荐（昨天和前天）
        for i, days_ago in enumerate([1, 2, 3]):
            rec = DailyRecommendation(
                id=f"daily-v2-history-{i+1}",
                poem_id=f"daily-v2-poem-00{i+1}",
                recommend_date=date.today() - timedelta(days=days_ago),
                reason=f"历史推荐{i+1}",
                reason_type="manual",
            )
            db.add(rec)
        await db.commit()

    resp = await client.get(
        "/api/v1/daily/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3
    # 按 date 倒序
    assert data["items"][0]["date"] >= data["items"][1]["date"]


@pytest.mark.asyncio
async def test_daily_history_pagination(client: AsyncClient):
    """分页参数生效。"""
    token = await _login_and_get_token(client, "daily_v2_page")

    async with async_session() as db:
        await _insert_test_poems(db)
        # 插入5条历史推荐
        for i in range(5):
            rec = DailyRecommendation(
                id=f"daily-v2-page-{i+1}",
                poem_id=f"daily-v2-poem-00{(i % 6) + 1}",
                recommend_date=date.today() - timedelta(days=i + 1),
                reason=f"分页测试{i+1}",
                reason_type="manual",
            )
            db.add(rec)
        await db.commit()

    # 第1页2条
    resp1 = await client.get(
        "/api/v1/daily/history?page=1&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["page"] == 1
    assert data1["page_size"] == 2
    assert len(data1["items"]) == 2

    # 第2页
    resp2 = await client.get(
        "/api/v1/daily/history?page=2&page_size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["page"] == 2
    # 两页的内容不应完全相同
    if data1["items"] and data2["items"]:
        assert data1["items"][0]["id"] != data2["items"][0]["id"]


@pytest.mark.asyncio
async def test_daily_today_with_recommend_service(client: AsyncClient):
    """今日推荐使用推荐引擎（无已有推荐时，引擎生成推荐）。"""
    token = await _login_and_get_token(client, "daily_v2_today")

    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()

    resp = await client.get(
        "/api/v1/daily/today",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "poem" in data
    assert data["poem"]["title"] != ""
    assert data["reason"] != ""
    assert data["can_switch"] is True
    assert data["switch_count"] == 0


@pytest.mark.asyncio
async def test_daily_switch_limit(client: AsyncClient):
    """换一首限制生效（最多5次非置顶换诗）。"""
    token = await _login_and_get_token(client, "daily_v2_switch")

    async with async_session() as db:
        await _insert_test_poems(db)
        # 创建今日置顶推荐
        rec = DailyRecommendation(
            id="daily-v2-switch-pinned",
            poem_id="daily-v2-poem-001",
            recommend_date=date.today(),
            reason="测试置顶",
            reason_type="manual",
            is_pinned=True,
        )
        db.add(rec)

        # 已换5次（非置顶） — 达到上限
        for i in range(5):
            switch_rec = DailyRecommendation(
                id=f"daily-v2-switch-{i+1}",
                poem_id=f"daily-v2-poem-00{(i % 6) + 1}",
                recommend_date=date.today(),
                reason=f"换诗{i+1}",
                reason_type="manual",
                is_pinned=False,
            )
            db.add(switch_rec)
        await db.commit()

    # 第6次换诗 should fail (5 non-pinned = limit reached)
    resp = await client.post(
        "/api/v1/daily/switch",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_daily_history_empty(client: AsyncClient):
    """无历史 → 空列表。"""
    token = await _login_and_get_token(client, "daily_v2_empty")

    resp = await client.get(
        "/api/v1/daily/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
