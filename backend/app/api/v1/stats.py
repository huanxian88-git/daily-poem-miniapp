"""统计汇总 API 路由：1个端点

需要 Bearer token 认证：
1. GET /stats/summary → 学习统计摘要（累计背诵/掌握/连续天数/今日）
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.recitation import Recitation
from app.schemas.stats import StatsSummaryResponse

router = APIRouter()


@router.get("/summary", response_model=StatsSummaryResponse)
async def get_stats_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学习统计摘要。

    统计维度：
    - total_recited:  用户累计参与背诵的诗词总数
    - total_mastered: 累计完全掌握的诗词数
    - streak_days:    连续背诵天数（基于 created_at 连续日期计算）
    - today_recited:  今日已开始或完成的背诵数
    """
    user_id = current_user.get("sub")
    today = date.today()

    # 1. 累计背诵总数（所有状态的非放弃记录）
    total_result = await db.execute(
        select(func.count(Recitation.id)).where(Recitation.user_id == user_id)
    )
    total_recited = total_result.scalar() or 0

    # 2. 累计掌握总数
    mastered_result = await db.execute(
        select(func.count(Recitation.id)).where(
            Recitation.user_id == user_id,
            Recitation.is_mastered == True,
        )
    )
    total_mastered = mastered_result.scalar() or 0

    # 3. 今日背诵数量
    today_dt_start = datetime(today.year, today.month, today.day, 0, 0, 0)
    today_dt_end = today_dt_start + timedelta(days=1)

    today_result = await db.execute(
        select(func.count(Recitation.id)).where(
            Recitation.user_id == user_id,
            Recitation.created_at >= today_dt_start,
            Recitation.created_at < today_dt_end,
        )
    )
    today_recited = today_result.scalar() or 0

    # 4. 连续背诵天数
    streak_days = await _calc_streak_days(db, user_id)

    return StatsSummaryResponse(
        total_recited=total_recited,
        total_mastered=total_mastered,
        streak_days=streak_days,
        today_recited=today_recited,
    )


async def _calc_streak_days(
    db: AsyncSession,
    user_id: str,
) -> int:
    """计算用户连续背诵天数。

    查询该用户每天至少有一条背诵记录的连续天数。
    通过 date(created_at) 分组去重后倒序检查连续性。

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        连续天数（0表示今天无记录）
    """
    # 使用 SQLAlchemy func.date 提取日期部分分组
    # 注意：SQLite 用 date() 函数，PostgreSQL 也兼容
    from sqlalchemy import func as sa_func

    result = await db.execute(
        select(sa_func.date(Recitation.created_at).label("recite_date"))
        .where(Recitation.user_id == user_id)
        .distinct()
        .order_by(sa_func.date(Recitation.created_at).desc())
    )
    dates_raw = result.all()

    if not dates_raw:
        return 0

    # 解析日期列表
    dates: list[date] = []
    for row in dates_raw:
        d = row[0]
        if isinstance(d, date):
            dates.append(d)
        elif hasattr(d, "date"):
            dates.append(d.date())
        elif isinstance(d, str):
            try:
                from datetime import datetime as dt
                dates.append(dt.strptime(d, "%Y-%m-%d").date())
            except (ValueError, TypeError):
                pass

    if not dates:
        return 0

    # 去重排序（确保从最新到最旧）
    dates = sorted(set(dates), reverse=True)

    today = date.today()
    yesterday = today - timedelta(days=1)

    # 如果最近一次不是今天或昨天，连续天数为0
    if dates[0] != today and dates[0] != yesterday:
        return 0

    # 从最新日期往前逐日验证连续性
    streak = 1
    check_date = dates[0]
    for d in dates[1:]:
        expected_prev = check_date - timedelta(days=1)
        if d == expected_prev:
            streak += 1
            check_date = expected_prev
        else:
            break

    return streak
