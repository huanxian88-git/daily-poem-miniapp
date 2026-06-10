"""复习调度服务层

基于艾宾浩斯遗忘曲线 SM-2 算法的复习管理：
- 获取今日复习队列
- 标记复习完成（动态调整间隔）
- 复习统计汇总
"""

from datetime import date, datetime, timedelta
from typing import Literal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recitation import Recitation
from app.models.review import ReviewSchedule
from app.models.poem import Poem
from app.schemas.review import (
    ReviewQueueItem,
    ReviewQueueResponse,
    ReviewDoneResponse,
    ReviewStatsResponse,
)

# 类型别名
SelfAssessment = Literal["easy", "good", "hard"]


async def get_review_queue(
    db: AsyncSession,
    user_id: str,
) -> ReviewQueueResponse:
    """获取今日复习队列。

    查询 next_review_date <= today 的所有复习计划，
    按 next_review_date 升序排列（越紧急越靠前）。

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        复习队列项列表及总数
    """
    today = date.today()

    result = await db.execute(
        select(ReviewSchedule)
        .where(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.next_review_date <= today,
        )
        .order_by(ReviewSchedule.next_review_date.asc())
    )
    schedules = result.scalars().all()

    items: list[ReviewQueueItem] = []
    for schedule in schedules:
        # 获取诗词标题
        poem_result = await db.execute(
            select(Poem.title).where(Poem.id == schedule.poem_id)
        )
        poem_title = poem_result.scalar_one_or_none() or "未知"

        # 计算紧急程度
        days_overdue = (today - schedule.next_review_date).days
        if days_overdue > 7:
            urgency = "high"
        elif days_overdue > 2:
            urgency = "medium"
        else:
            urgency = "low"

        items.append(ReviewQueueItem(
            poem_id=schedule.poem_id,
            poem_title=poem_title,
            next_review_date=schedule.next_review_date,
            review_count=schedule.review_count,
            urgency=urgency,
        ))

    return ReviewQueueResponse(items=items, total=len(items))


async def mark_review_done(
    db: AsyncSession,
    user_id: str,
    poem_id: str,
    self_assessment: SelfAssessment,
) -> ReviewDoneResponse:
    """标记复习完成并应用 SM-2 算法更新下次复习时间。

    SM-2 算法规则：
    - easy:   ease_factor += 0.15, interval *= ease_factor
    - good:   interval *= ease_factor（ease不变）
    - hard:   ease_factor = max(1.3, ease - 0.2), interval = max(1, int(interval * 0.6))

    Args:
        db: 数据库会话
        user_id: 用户ID
        poem_id: 诗词ID
        self_assessment: 自评难度（easy/good/hard）

    Returns:
        下次复习日期和间隔天数

    Raises:
        ValueError: 复习计划不存在或不属于当前用户
    """
    # 查询复习计划
    result = await db.execute(
        select(ReviewSchedule).where(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.poem_id == poem_id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise ValueError("未找到该诗词的复习计划")

    # 应用 SM-2 算法
    ease = schedule.ease_factor
    interval = schedule.interval_days

    if self_assessment == "easy":
        # 表现优秀：提高易度因子和间隔
        ease = ease + 0.15
        interval = int(interval * ease)
    elif self_assessment == "good":
        # 表现一般：间隔正常增长
        interval = int(interval * ease)
    elif self_assessment == "hard":
        # 困难：降低易度因子，缩短间隔
        ease = max(1.3, ease - 0.2)
        interval = max(1, int(interval * 0.6))
    else:
        raise ValueError(f"无效的自评值: {self_assessment}")

    # 更新计划
    now = datetime.utcnow()
    next_review = date.today() + timedelta(days=interval)

    schedule.ease_factor = ease
    schedule.interval_days = interval
    schedule.next_review_date = next_review
    schedule.review_count += 1
    schedule.last_reviewed_at = now

    await db.commit()

    return ReviewDoneResponse(
        next_review_date=next_review,
        interval_days=interval,
    )


async def get_review_stats(
    db: AsyncSession,
    user_id: str,
) -> ReviewStatsResponse:
    """获取复习统计摘要。

    统计维度：
    - total:     总复习计划数（含已掌握+复习中）
    - mastered:  三关通过且长期稳定复习的用户数
    - reviewing: 正在复习中的数量
    - today_due: 今日到期需复习数量

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        复习统计摘要
    """
    today = date.today()

    # 总计划数
    total_result = await db.execute(
        select(func.count(ReviewSchedule.id)).where(
            ReviewSchedule.user_id == user_id
        )
    )
    total = total_result.scalar() or 0

    # 已掌握（背诵状态为 memorized 或 mastered 且复习次数>=3）
    mastered_result = await db.execute(
        select(func.count(Recitation.id)).where(
            Recitation.user_id == user_id,
            Recitation.is_mastered == True,
        )
    )
    mastered = mastered_result.scalar() or 0

    # 复习中（有复习计划且非已完全掌握）
    reviewing_result = await db.execute(
        select(func.count(ReviewSchedule.id)).where(
            ReviewSchedule.user_id == user_id,
        )
    )
    reviewing = reviewing_result.scalar() or 0

    # 今日到期
    today_due_result = await db.execute(
        select(func.count(ReviewSchedule.id)).where(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.next_review_date <= today,
        )
    )
    today_due = today_due_result.scalar() or 0

    return ReviewStatsResponse(
        total=total,
        mastered=mastered,
        reviewing=reviewing,
        today_due=today_due,
    )
