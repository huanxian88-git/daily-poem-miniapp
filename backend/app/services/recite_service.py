"""背诵核心业务服务层

提供背诵全流程的核心业务逻辑：
- 开始/放弃背诵
- 三关检查（补阙填词、排序归位、语音背诵）
- 成诵判定
- 背诵列表与结果查询
"""

import json
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poem import Poem
from app.models.recitation import Recitation, RecitationAttempt
from app.models.review import ReviewSchedule
from app.schemas.recitation import (
    RecitationStartResponse,
    FillCheckResponse,
    SortCheckResponse,
    VoiceCheckResponse,
    RecitationResultResponse,
    RecitationListResponse,
    RecitationBrief,
)
from app.models.user import _uuid_str


# ---- 并发守卫常量 ----
MAX_CONCURRENT_RECITING = 2  # 最大同时背诵数


async def start_recite(
    db: AsyncSession,
    user_id: str,
    poem_id: str,
    confirmed: bool = False,
) -> RecitationStartResponse:
    """开始背诵一首诗词。

    流程：
    1. 校验诗词是否存在
    2. 检查该诗词是否已在背诵中（避免重复）
    3. 并发守卫：查询用户当前在背数（status=reciting）
       - 0首 → 自由开始
       - 1首 → 返回 warm_reminder=True（提醒但允许）
       - >=2首 → 未确认时拦截，确认后允许
    4. 创建 Recitation 记录（status=reciting）

    Args:
        db: 数据库会话
        user_id: 用户ID
        poem_id: 要背诵的诗词ID
        confirmed: 用户是否确认继续（并发数>=1时的二次确认）

    Returns:
        包含 recitation_id、stage、warm_reminder 的响应

    Raises:
        ValueError: 诗词不存在或并发超限未确认
    """
    # 1. 校验诗词存在
    poem_result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = poem_result.scalar_one_or_none()
    if not poem:
        raise ValueError(f"诗词不存在: {poem_id}")

    # 2. 检查是否已在该诗的背诵中
    existing_result = await db.execute(
        select(Recitation).where(
            Recitation.user_id == user_id,
            Recitation.poem_id == poem_id,
            Recitation.status == "reciting",
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise ValueError("你正在背诵这首诗词，请先完成或放弃")

    # 3. 并发守卫
    concurrent_result = await db.execute(
        select(func.count(Recitation.id)).where(
            Recitation.user_id == user_id,
            Recitation.status == "reciting",
        )
    )
    concurrent_count = concurrent_result.scalar() or 0

    warm_reminder: Optional[bool] = None

    if concurrent_count >= MAX_CONCURRENT_RECITING and not confirmed:
        raise ValueError(f"最多同时背诵{MAX_CONCURRENT_RECITING}首，请先完成或放弃其中一首")
    elif concurrent_count > 0 and concurrent_count < MAX_CONCURRENT_RECITING:
        warm_reminder = True

    # 4. 创建背诵记录
    now = datetime.utcnow()
    recitation = Recitation(
        id=_uuid_str(),
        user_id=user_id,
        poem_id=poem_id,
        status="reciting",
        recite_stage="fill",
        started_at=now,
    )
    db.add(recitation)
    await db.commit()
    await db.refresh(recitation)

    return RecitationStartResponse(
        recitation_id=recitation.id,
        stage="fill",
        warm_reminder=warm_reminder,
    )


async def fill_check(
    db: AsyncSession,
    recitation_id: str,
    answers: list[dict],
) -> FillCheckResponse:
    """补阙填词检查。

    从 Poem.content_lines 中按 pos 挖空，逐字比对用户答案。
    评分公式：正确字数 / 总字数 × 100

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID
        answers: 用户填写的答案 [{pos: int, word: str}, ...]

    Returns:
        score、pass、detail

    Raises:
        ValueError: 记录不存在或状态异常
    """
    # 获取背诵记录
    recitation = await _get_active_recitation(db, recitation_id)

    # 获取诗词内容行
    poem_result = await db.execute(select(Poem).where(Poem.id == recitation.poem_id))
    poem = poem_result.scalar_one_or_none()
    if not poem:
        raise ValueError("关联的诗词不存在")

    # 解析 content_lines
    content_lines: list[str] = []
    if poem.content_lines:
        try:
            content_lines = json.loads(poem.content_lines)
        except (json.JSONDecodeError, TypeError):
            content_lines = [poem.content] if poem.content else []

    if not content_lines:
        raise ValueError("诗词无可用内容行")

    total_chars = sum(len(line) for line in content_lines)
    correct_chars = 0
    answer_details: list[dict] = []

    for answer in answers:
        pos = answer.get("pos", 0)
        word = str(answer.get("word", ""))
        expected_word = ""

        # 根据 pos 定位到对应行的字符
        char_idx = 0
        for line_idx, line in enumerate(content_lines):
            for c_idx, ch in enumerate(line):
                if char_idx == pos:
                    expected_word = ch
                    break
                char_idx += 1
            if expected_word:
                break
            char_idx += (1 if line_idx < len(content_lines) - 1 else 0)

        is_correct = word == expected_word
        if is_correct:
            correct_chars += 1

        answer_details.append({
            "pos": pos,
            "expected": expected_word,
            "actual": word,
            "correct": is_correct,
        })

    # 计算得分
    score = int((correct_chars / max(total_chars, 1)) * 100)
    is_pass = score >= 60

    detail = {
        "total_chars": total_chars,
        "correct_chars": correct_chars,
        "answers": answer_details,
    }

    # 保存尝试记录
    attempt = RecitationAttempt(
        id=_uuid_str(),
        recitation_id=recitation_id,
        stage="fill",
        score=score,
        detail=json.dumps(detail, ensure_ascii=False),
    )
    db.add(attempt)

    # 更新背诵记录
    recitation.fill_score = score
    recitation.attempt_count += 1
    recitation.updated_at = datetime.utcnow()

    await db.commit()

    return FillCheckResponse(score=score, pass_=is_pass, detail=detail)


async def sort_check(
    db: AsyncSession,
    recitation_id: str,
    order: list[int],
) -> SortCheckResponse:
    """排序归位检查。

    将用户排列的行顺序与原始 content_lines 顺序比对。
    评分公式：正确位置数 / 总行数 × 100

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID
        order: 用户排列的行索引列表

    Returns:
        score、pass、detail

    Raises:
        ValueError: 记录不存在或状态异常
    """
    recitation = await _get_active_recitation(db, recitation_id)

    # 获取诗词内容行
    poem_result = await db.execute(select(Poem).where(Poem.id == recitation.poem_id))
    poem = poem_result.scalar_one_or_none()
    if not poem:
        raise ValueError("关联的诗词不存在")

    content_lines: list[str] = []
    if poem.content_lines:
        try:
            content_lines = json.loads(poem.content_lines)
        except (json.JSONDecodeError, TypeError):
            content_lines = [poem.content] if poem.content else []

    if not content_lines:
        raise ValueError("诗词无可用内容行")

    total_lines = len(content_lines)

    # 比对顺序
    correct_positions = 0
    position_details: list[dict] = []

    for user_pos, original_idx in enumerate(order):
        is_correct = user_pos == original_idx
        if is_correct:
            correct_positions += 1
        position_details.append({
            "user_position": user_pos,
            "original_index": original_idx,
            "correct": is_correct,
        })

    score = int((correct_positions / max(total_lines, 1)) * 100)
    is_pass = score >= 60

    detail = {
        "total_lines": total_lines,
        "correct_positions": correct_positions,
        "positions": position_details,
    }

    # 保存尝试记录
    attempt = RecitationAttempt(
        id=_uuid_str(),
        recitation_id=recitation_id,
        stage="sort",
        score=score,
        detail=json.dumps(detail, ensure_ascii=False),
    )
    db.add(attempt)

    # 更新背诵记录
    recitation.sort_score = score
    recitation.attempt_count += 1
    recitation.updated_at = datetime.utcnow()

    await db.commit()

    return SortCheckResponse(score=score, pass_=is_pass, detail=detail)


async def voice_check(
    db: AsyncSession,
    recitation_id: str,
    recognized_text: str,
) -> VoiceCheckResponse:
    """语音背诵检查（阶段3 mock 版本）。

    阶段3不接真实ASR，直接使用前端传入的recognized_text进行评分。
    字级比对：将 recognized_text 与 content_lines 拼接后的全文比对。
    评分公式：匹配字数 / 总字数 × 100

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID
        recognized_text: ASR识别出的文本（阶段3为前端传入）

    Returns:
        score、detail、recognized_text

    Raises:
        ValueError: 记录不存在或状态异常
    """
    recitation = await _get_active_recitation(db, recitation_id)

    # 获取诗词全文
    poem_result = await db.execute(select(Poem).where(Poem.id == recitation.poem_id))
    poem = poem_result.scalar_one_or_none()
    if not poem:
        raise ValueError("关联的诗词不存在")

    # 构建标准全文（优先用content，备用拼接lines）
    full_text = poem.content or ""

    if not full_text and poem.content_lines:
        try:
            lines = json.loads(poem.content_lines)
            full_text = "".join(lines)
        except (json.JSONDecodeError, TypeError):
            pass

    if not full_text:
        raise ValueError("诗词无可用文本")

    # 字级比对
    total_chars = len(full_text)
    correct_chars = 0
    char_details: list[dict] = []

    # 简单的字序匹配
    min_len = min(len(recognized_text), total_chars)
    for i in range(min_len):
        is_match = recognized_text[i] == full_text[i]
        if is_match:
            correct_chars += 1
        char_details.append({
            "position": i,
            "expected": full_text[i] if i < total_chars else "",
            "actual": recognized_text[i] if i < len(recognized_text) else "",
            "match": is_match,
        })

    # 处理长度差异部分
    extra_chars = max(len(recognized_text), total_chars) - min_len
    for j in range(extra_chars):
        base_idx = min_len + j
        exp_char = full_text[base_idx] if base_idx < total_chars else ""
        act_char = recognized_text[base_idx] if base_idx < len(recognized_text) else ""
        char_details.append({
            "position": base_idx,
            "expected": exp_char,
            "actual": act_char,
            "match": False,
        })

    score = int((correct_chars / max(total_chars, 1)) * 100)
    is_pass = score >= 60

    detail = {
        "total_chars": total_chars,
        "correct_chars": correct_chars,
        "input_length": len(recognized_text),
        "chars": char_details[:50],  # 截断避免过大
    }

    # 保存尝试记录
    attempt = RecitationAttempt(
        id=_uuid_str(),
        recitation_id=recitation_id,
        stage="voice",
        score=score,
        detail=json.dumps(detail, ensure_ascii=False),
    )
    db.add(attempt)

    # 更新背诵记录
    recitation.voice_score = score
    recitation.attempt_count += 1
    recitation.updated_at = datetime.utcnow()

    await db.commit()

    return VoiceCheckResponse(score=score, detail=detail, recognized_text=recognized_text)


async def check_mastery(db: AsyncSession, recitation_id: str) -> bool:
    """成诵判定。

    当三关分数都 >= 60 时判定为已掌握（is_mastered=True），
    自动更新状态为 memorized，并创建 ReviewSchedule（艾宾浩斯初始参数）。

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID

    Returns:
        是否达到掌握标准
    """
    recitation = await _get_active_recitation(db, recitation_id)

    fill_ok = (recitation.fill_score or 0) >= 60
    sort_ok = (recitation.sort_score or 0) >= 60
    voice_ok = (recitation.voice_score or 0) >= 60

    if fill_ok and sort_ok and voice_ok:
        now = datetime.utcnow()
        recitation.is_mastered = True
        recitation.status = "memorized"
        recitation.mastered_at = now
        recitation.updated_at = now

        # 创建复习计划（SM-2 初始参数）
        schedule = ReviewSchedule(
            id=_uuid_str(),
            user_id=recitation.user_id,
            poem_id=recitation.poem_id,
            next_review_date=date.today(),  # 今日即可复习
            review_count=0,
            ease_factor=2.5,
            interval_days=1,
        )
        db.add(schedule)

        await db.commit()
        return True

    return False


async def abandon_recite(db: AsyncSession, recitation_id: str) -> None:
    """放弃背诵。

    删除指定的 Recitation 记录及其关联的所有 Attempt。

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID

    Raises:
        ValueError: 记录不存在
    """
    result = await db.execute(
        select(Recitation).where(
            Recitation.id == recitation_id,
            Recitation.status == "reciting",
        )
    )
    recitation = result.scalar_one_or_none()
    if not recitation:
        raise ValueError("背诵记录不存在或已完成")

    # 删除关联的尝试记录
    await db.execute(
        delete(RecitationAttempt).where(
            RecitationAttempt.recitation_id == recitation_id
        )
    )

    # 删除背诵记录
    await db.execute(
        delete(Recitation).where(Recitation.id == recitation_id)
    )

    await db.commit()


async def get_recite_list(
    db: AsyncSession,
    user_id: str,
) -> RecitationListResponse:
    """获取用户当前在背列表。

    查询 status='reciting' 的所有 Recitation 记录。

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        在背列表及总数
    """
    result = await db.execute(
        select(Recitation)
        .where(Recitation.user_id == user_id, Recitation.status == "reciting")
        .order_by(Recitation.started_at.desc())
    )
    recitations = result.scalars().all()

    items: list[RecitationBrief] = []
    for r in recitations:
        # 获取诗词标题
        poem_result = await db.execute(select(Poem.title).where(Poem.id == r.poem_id))
        poem_title = poem_result.scalar_one_or_none() or "未知"

        items.append(RecitationBrief(
            id=r.id,
            poem_id=r.poem_id,
            poem_title=poem_title,
            status=r.status,
            scores={
                "fill": r.fill_score,
                "sort": r.sort_score,
                "voice": r.voice_score,
            },
            created_at=r.created_at.isoformat() if r.created_at else "",
        ))

    return RecitationListResponse(items=items, total=len(items))


async def get_recite_result(
    db: AsyncSession,
    recitation_id: str,
) -> RecitationResultResponse:
    """获取背诵完整结果（三关总览）。

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID

    Returns:
        背诵详情+三关得分+是否掌握

    Raises:
        ValueError: 记录不存在
    """
    result = await db.execute(
        select(Recitation).where(Recitation.id == recitation_id)
    )
    recitation = result.scalar_one_or_none()
    if not recitation:
        raise ValueError("背诵记录不存在")

    # 获取诗词标题
    poem_result = await db.execute(select(Poem.title).where(Poem.id == recitation.poem_id))
    poem_title = poem_result.scalar_one_or_none() or "未知"

    return RecitationResultResponse(
        recitation_id=recitation.id,
        poem_id=recitation.poem_id,
        poem_title=poem_title,
        status=recitation.status,
        is_mastered=recitation.is_mastered,
        fill_score=recitation.fill_score,
        sort_score=recitation.sort_score,
        voice_score=recitation.voice_score,
        mastered_at=recitation.mastered_at.isoformat() if recitation.mastered_at else None,
        created_at=recitation.created_at.isoformat() if recitation.created_at else "",
    )


# ---- 内部辅助函数 ----

async def _get_active_recitation(
    db: AsyncSession,
    recitation_id: str,
) -> Recitation:
    """获取活跃的背诵记录（校验存在性和状态）。

    Args:
        db: 数据库会话
        recitation_id: 背诵记录ID

    Returns:
        背诵记录对象

    Raises:
        ValueError: 不存在或非活跃状态
    """
    result = await db.execute(
        select(Recitation).where(Recitation.id == recitation_id)
    )
    recitation = result.scalar_one_or_none()
    if not recitation:
        raise ValueError("背诵记录不存在")
    if recitation.status != "reciting":
        raise ValueError("该背诵已完成或已放弃")
    return recitation
