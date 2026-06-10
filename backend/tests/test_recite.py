"""背诵模块 API 测试 —— 22个用例覆盖完整背诵流程。

覆盖功能：
- 开始背诵（并发守卫、暖提醒、硬拦截、重复检测）
- 补阙填词检查（通过/失败/部分正确/不存在/无权限）
- 排序归位检查（通过/失败/部分正确）
- 语音背诵检查（通过/失败）
- 成诵判定（三关全过/部分通过）
- 在背列表 / 背诵结果 / 放弃背诵
"""

import json
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import decode_token
from app.models.poem import Poem
from app.models.recitation import Recitation
from app.models.review import ReviewSchedule
from app.models.user import _uuid_str
from app.services import recite_service


# ---- 辅助函数 ----

def _make_fill_answers(text: str, content_lines: list[str], correct: bool = True) -> list[dict]:
    """构造 fill_check 的 answers 列表。

    fill_check 服务中，char_idx 的计算方式：
    - 每个字符占一个 pos
    - 行间有一个间隔位（不对应任何字符）
    
    对于「静夜思」（4行×6字）：
    - 行0（床前明月光，）: pos 0-5
    - 间隔位: pos 6
    - 行1（疑是地上霜。）: pos 7-12
    - 间隔位: pos 13
    - 行2（举头望明月，）: pos 14-19
    - 间隔位: pos 20
    - 行3（低头思故乡。）: pos 21-26
    """
    answers = []
    pos = 0
    for line_idx, line in enumerate(content_lines):
        for ch in line:
            word = ch if correct else "错"
            answers.append({"pos": pos, "word": word})
            pos += 1
        # 行间间隔位（最后一行后不需要）
        if line_idx < len(content_lines) - 1:
            pos += 1
    return answers


# ---- 测试数据辅助 ----


async def _insert_test_poems(db: AsyncSession):
    """插入5首测试诗词。"""
    poems = [
        Poem(
            id="recite-poem-001",
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
            id="recite-poem-002",
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
            id="recite-poem-003",
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
            id="recite-poem-004",
            title="悯农",
            author="李绅",
            dynasty="唐",
            content="锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。",
            content_lines=json.dumps(
                ["锄禾日当午，", "汗滴禾下土。", "谁知盘中餐，", "粒粒皆辛苦。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            tags="意象:烈日|主题:悯农|场景:农田",
            status="active",
        ),
        Poem(
            id="recite-poem-005",
            title="咏鹅",
            author="骆宾王",
            dynasty="唐",
            content="鹅鹅鹅，曲项向天歌。白毛浮绿水，红掌拨清波。",
            content_lines=json.dumps(
                ["鹅鹅鹅，", "曲项向天歌。", "白毛浮绿水，", "红掌拨清波。"],
                ensure_ascii=False,
            ),
            difficulty=1,
            tags="意象:鹅|主题:咏物|场景:水边",
            status="active",
        ),
    ]
    for p in poems:
        db.add(p)
    await db.flush()


async def _login_and_get_token(client: AsyncClient, code: str = "recite_test_user") -> str:
    """登录并返回 access_token。"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"code": code},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _get_user_id_from_token(token: str) -> str:
    """从 JWT token 中解析 user_id。"""
    payload = decode_token(token)
    assert payload is not None
    return payload["sub"]


async def _setup_poems_and_get_token(client: AsyncClient, code: str = "recite_test_user") -> str:
    """插入诗词 + 登录，返回 token。"""
    async with async_session() as db:
        await _insert_test_poems(db)
        await db.commit()
    return await _login_and_get_token(client, code)


# ---- 开始背诵 (start_recite) ----


@pytest.mark.asyncio
async def test_recite_start_success(client: AsyncClient):
    """正常开始背诵（0首在背 → 直接创建）。"""
    token = await _setup_poems_and_get_token(client, "recite_start_01")

    resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001", "confirmed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "recitation_id" in data
    assert data["stage"] == "fill"
    assert data["warm_reminder"] is None


@pytest.mark.asyncio
async def test_recite_start_warm_reminder(client: AsyncClient):
    """1首在背 → 返回 warm_reminder=True。"""
    token = await _setup_poems_and_get_token(client, "recite_start_02")

    # 先开始背诵第一首
    resp1 = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 200

    # 再开始第二首，应触发 warm_reminder
    resp2 = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-002"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["warm_reminder"] is True


@pytest.mark.asyncio
async def test_recite_start_confirmed(client: AsyncClient):
    """1首在背 → confirmed=True → 允许。"""
    token = await _setup_poems_and_get_token(client, "recite_start_03")

    # 先开始第一首
    await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # confirmed=True 开始第二首
    resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-002", "confirmed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "recitation_id" in data


@pytest.mark.asyncio
async def test_recite_start_hard_block(client: AsyncClient):
    """2首在背 → 硬拦截(400)。"""
    token = await _setup_poems_and_get_token(client, "recite_start_04")

    # 开始两首
    await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-002"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 尝试第三首，应被拦截
    resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-003"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_recite_start_unauthorized(client: AsyncClient):
    """无 token → 401。"""
    resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_recite_start_duplicate_poem(client: AsyncClient):
    """同一首诗已在背 → 返回400错误。"""
    token = await _setup_poems_and_get_token(client, "recite_start_05")

    # 开始背诵第一首
    resp1 = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 200

    # 再背诵同一首 → 报错
    resp2 = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 400


# ---- 补阙填词 (fill_check) ----


@pytest.mark.asyncio
async def test_fill_check_pass(client: AsyncClient):
    """正确填写 → score>=60, pass=True。"""
    token = await _setup_poems_and_get_token(client, "recite_fill_01")

    # 开始背诵
    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 使用 _make_fill_answers 辅助函数构造正确答案
    content_lines = ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"]
    correct_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    answers = _make_fill_answers(correct_text, content_lines, correct=True)

    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/fill",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] >= 60
    assert data["pass"] is True


@pytest.mark.asyncio
async def test_fill_check_fail(client: AsyncClient):
    """全部填错 → score<60, pass=False。"""
    token = await _setup_poems_and_get_token(client, "recite_fill_02")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 使用 _make_fill_answers 构造全部填错的答案
    content_lines = ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"]
    correct_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    answers = _make_fill_answers(correct_text, content_lines, correct=False)

    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/fill",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] < 60
    assert data["pass"] is False


@pytest.mark.asyncio
async def test_fill_check_partial(client: AsyncClient):
    """部分正确 → score 介于中间。"""
    token = await _setup_poems_and_get_token(client, "recite_fill_03")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 使用 _make_fill_answers 构造部分正确的答案
    content_lines = ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"]
    correct_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    all_correct = _make_fill_answers(correct_text, content_lines, correct=True)

    # 前12个正确，后12个填错 → 12/24=50%
    answers = []
    for i, ans in enumerate(all_correct):
        if i < 12:
            answers.append(ans)
        else:
            answers.append({"pos": ans["pos"], "word": "错"})

    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/fill",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # 12/24 = 50，score < 60
    assert 0 < data["score"] < 60
    assert data["pass"] is False


@pytest.mark.asyncio
async def test_fill_check_not_found(client: AsyncClient):
    """recitation_id 不存在 → 400（service ValueError → API 400）。"""
    token = await _setup_poems_and_get_token(client, "recite_fill_04")

    fake_id = "nonexistent-recite-id"
    resp = await client.post(
        f"/api/v1/recite/{fake_id}/fill",
        json={"answers": [{"pos": 0, "word": "床"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    # service raises ValueError → API converts to 400
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_fill_check_unauthorized(client: AsyncClient):
    """无 token → 401。"""
    resp = await client.post(
        "/api/v1/recite/fake-id/fill",
        json={"answers": [{"pos": 0, "word": "床"}]},
    )
    assert resp.status_code == 401


# ---- 排序归位 (sort_check) ----


@pytest.mark.asyncio
async def test_sort_check_pass(client: AsyncClient):
    """正确排序 → score>=60, pass=True。"""
    token = await _setup_poems_and_get_token(client, "recite_sort_01")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 正确顺序（0,1,2,3 — 4行内容）
    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/sort",
        json={"order": [0, 1, 2, 3]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] >= 60
    assert data["pass"] is True


@pytest.mark.asyncio
async def test_sort_check_fail(client: AsyncClient):
    """完全乱序 → score<60, pass=False。"""
    token = await _setup_poems_and_get_token(client, "recite_sort_02")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 完全乱序
    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/sort",
        json={"order": [3, 2, 1, 0]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] < 60
    assert data["pass"] is False


@pytest.mark.asyncio
async def test_sort_check_partial(client: AsyncClient):
    """部分正确 → 中间分数。"""
    token = await _setup_poems_and_get_token(client, "recite_sort_03")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 部分正确（0,2,1,3 — 第1、4行正确 → 2/4=50）
    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/sort",
        json={"order": [0, 2, 1, 3]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 50
    assert data["pass"] is False


# ---- 语音背诵 (voice_check) ----


@pytest.mark.asyncio
async def test_voice_check_pass(client: AsyncClient):
    """模拟 ASR 文字正确 → score>=60。"""
    token = await _setup_poems_and_get_token(client, "recite_voice_01")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 完全正确的全文
    correct_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/voice",
        json={"recognized_text": correct_text},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] >= 60


@pytest.mark.asyncio
async def test_voice_check_fail(client: AsyncClient):
    """模拟 ASR 文字全错 → score<60。"""
    token = await _setup_poems_and_get_token(client, "recite_voice_02")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 完全错误的文字
    wrong_text = "这是一段完全错误的文字用于测试语音背诵检查失败的情况。"
    resp = await client.post(
        f"/api/v1/recite/{recitation_id}/voice",
        json={"recognized_text": wrong_text},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] < 60


# ---- 成诵判定 (mastery) — 通过 service 层测试 ----


@pytest.mark.asyncio
async def test_mastery_all_pass(client: AsyncClient):
    """三关都过 → is_mastered=True, 自动创建 ReviewSchedule。"""
    token = await _setup_poems_and_get_token(client, "recite_mastery_01")
    user_id = _get_user_id_from_token(token)

    # 直接通过 service 层创建背诵记录并完成三关
    async with async_session() as db:
        # 开始背诵
        start_result = await recite_service.start_recite(
            db=db, user_id=user_id, poem_id="recite-poem-001",
        )
        recitation_id = start_result.recitation_id

        # 通过补阙填词（使用 _make_fill_answers 构造正确答案）
        content_lines = ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"]
        correct_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
        fill_answers = _make_fill_answers(correct_text, content_lines, correct=True)
        fill_result = await recite_service.fill_check(
            db=db, recitation_id=recitation_id, answers=fill_answers,
        )
        assert fill_result.pass_ is True

        # 通过排序归位
        sort_result = await recite_service.sort_check(
            db=db, recitation_id=recitation_id, order=[0, 1, 2, 3],
        )
        assert sort_result.pass_ is True

        # 通过语音背诵
        voice_result = await recite_service.voice_check(
            db=db, recitation_id=recitation_id,
            recognized_text="床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        )
        assert voice_result.score >= 60

        # 执行成诵判定
        is_mastered = await recite_service.check_mastery(db, recitation_id)
        assert is_mastered is True

        # 验证 ReviewSchedule 已创建
        from sqlalchemy import select
        schedule_result = await db.execute(
            select(ReviewSchedule).where(
                ReviewSchedule.user_id == user_id,
                ReviewSchedule.poem_id == "recite-poem-001",
            )
        )
        schedule = schedule_result.scalar_one_or_none()
        assert schedule is not None
        assert schedule.ease_factor == 2.5
        assert schedule.interval_days == 1


@pytest.mark.asyncio
async def test_mastery_partial_pass(client: AsyncClient):
    """只过两关 → is_mastered=False。"""
    token = await _setup_poems_and_get_token(client, "recite_mastery_02")
    user_id = _get_user_id_from_token(token)

    async with async_session() as db:
        start_result = await recite_service.start_recite(
            db=db, user_id=user_id, poem_id="recite-poem-001",
        )
        recitation_id = start_result.recitation_id

        # 通过排序
        await recite_service.sort_check(
            db=db, recitation_id=recitation_id, order=[0, 1, 2, 3],
        )

        # 通过语音
        await recite_service.voice_check(
            db=db, recitation_id=recitation_id,
            recognized_text="床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        )

        # 不通过补阙填词（使用 _make_fill_answers 构造全部填错的答案）
        content_lines = ["床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"]
        correct_text = "床前明月光，疑是地上霜。举头望明月，低头思故乡。"
        wrong_answers = _make_fill_answers(correct_text, content_lines, correct=False)
        await recite_service.fill_check(
            db=db, recitation_id=recitation_id, answers=wrong_answers,
        )

        # 执行成诵判定
        is_mastered = await recite_service.check_mastery(db, recitation_id)
        assert is_mastered is False


# ---- 其他 ----


@pytest.mark.asyncio
async def test_recite_list(client: AsyncClient):
    """获取在背列表。"""
    token = await _setup_poems_and_get_token(client, "recite_list_01")

    # 开始背诵2首
    await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-002"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        "/api/v1/recite/list",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_recite_result(client: AsyncClient):
    """获取背诵结果。"""
    token = await _setup_poems_and_get_token(client, "recite_result_01")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    resp = await client.get(
        f"/api/v1/recite/{recitation_id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recitation_id"] == recitation_id
    assert data["poem_title"] == "静夜思"
    assert data["status"] == "reciting"
    assert data["is_mastered"] is False


@pytest.mark.asyncio
async def test_recite_abandon(client: AsyncClient):
    """放弃背诵 → 列表中不再有。"""
    token = await _setup_poems_and_get_token(client, "recite_abandon_01")

    start_resp = await client.post(
        "/api/v1/recite/start",
        json={"poem_id": "recite-poem-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    recitation_id = start_resp.json()["recitation_id"]

    # 放弃
    abandon_resp = await client.post(
        f"/api/v1/recite/{recitation_id}/abandon",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert abandon_resp.status_code == 204

    # 验证列表中不再有
    list_resp = await client.get(
        "/api/v1/recite/list",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_recite_abandon_not_found(client: AsyncClient):
    """放弃不存在的记录 → 404。"""
    token = await _setup_poems_and_get_token(client, "recite_abandon_02")

    resp = await client.post(
        "/api/v1/recite/nonexistent-id/abandon",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
