"""每日推荐 API：今日推荐 + 换一首"""

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.poem import Poem
from app.models.recommendation import DailyRecommendation
from app.models.favorite import Favorite
from app.schemas.daily import DailyTodayResponse, DailySwitchResponse
from app.schemas.poem import PoemDetail
from app.api.v1.poems import _parse_tags, _get_textbook_info

router = APIRouter()


async def _poem_to_detail(
    db: AsyncSession, poem: Poem, user_id: str | None = None
) -> PoemDetail:
    """将诗词模型转为详情响应"""
    content_lines = None
    if poem.content_lines:
        try:
            content_lines = json.loads(poem.content_lines)
        except (json.JSONDecodeError, TypeError):
            pass

    is_favorited = False
    textbook_info = None
    if user_id:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.poem_id == poem.id,
            )
        )
        is_favorited = fav_result.scalar_one_or_none() is not None
        textbook_info = await _get_textbook_info(db, poem.id)

    return PoemDetail(
        id=poem.id,
        title=poem.title,
        author=poem.author,
        dynasty=poem.dynasty,
        content=poem.content,
        content_lines=content_lines,
        annotation=poem.annotation,
        translation=poem.translation,
        background=poem.background,
        difficulty=poem.difficulty,
        tags=poem.tags,
        tags_parsed=_parse_tags(poem.tags) if poem.tags else None,
        scene_type=poem.scene_type,
        scene_desc=poem.scene_desc,
        scene_image_url=poem.scene_image_url,
        is_favorited=is_favorited,
        textbook_info=textbook_info,
    )


@router.get("/today", response_model=DailyTodayResponse)
async def get_daily_today(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日推荐诗词"""
    user_id = current_user.get("sub")
    today = date.today()

    # 查询今日推荐（优先取置顶的）
    rec_result = await db.execute(
        select(DailyRecommendation)
        .where(DailyRecommendation.recommend_date == today)
        .order_by(DailyRecommendation.is_pinned.desc(), DailyRecommendation.created_at.desc())
        .limit(1)
    )
    rec = rec_result.scalar_one_or_none()

    # 如果今天没有推荐，随机取一首
    if not rec:
        poem_result = await db.execute(
            select(Poem).order_by(Poem.recite_count.desc()).limit(1)
        )
        poem = poem_result.scalar_one_or_none()
        if not poem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无诗词数据",
            )
        detail = await _poem_to_detail(db, poem, user_id)
        return DailyTodayResponse(
            poem=detail,
            reason="今日为你推荐这首经典名篇",
            reason_type="manual",
            can_switch=True,
            switch_count=0,
        )

    # 获取关联诗词
    poem_result = await db.execute(select(Poem).where(Poem.id == rec.poem_id))
    poem = poem_result.scalar_one_or_none()
    if not poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="推荐诗词不存在",
        )

    detail = await _poem_to_detail(db, poem, user_id)

    # 计算今日已换次数（当天非置顶推荐数 = 已换次数）
    count_result = await db.execute(
        select(DailyRecommendation).where(
            DailyRecommendation.recommend_date == today,
            DailyRecommendation.is_pinned == False,
        )
    )
    non_pinned_count = len(count_result.scalars().all())
    # 首次推荐不计入换诗次数
    switch_count = max(0, non_pinned_count)

    return DailyTodayResponse(
        poem=detail,
        reason=rec.reason or "今日为你推荐这首诗词",
        reason_type=rec.reason_type,
        can_switch=switch_count < 5,  # 阶段2放宽限制，最多换5次
        switch_count=switch_count,
    )


@router.post("/switch", response_model=DailySwitchResponse)
async def switch_daily_poem(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """换一首推荐诗词"""
    user_id = current_user.get("sub")
    today = date.today()

    # 检查今日已换次数
    count_result = await db.execute(
        select(DailyRecommendation).where(
            DailyRecommendation.recommend_date == today,
            DailyRecommendation.is_pinned == False,
        )
    )
    switch_count = len(count_result.scalars().all())
    if switch_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今日换诗次数已达上限",
        )

    # 获取已推荐过的诗词ID列表
    used_result = await db.execute(
        select(DailyRecommendation).where(
            DailyRecommendation.recommend_date == today
        )
    )
    used_poem_ids = [r.poem_id for r in used_result.scalars().all()]

    # 选一首未推荐过的诗词
    query = select(Poem)
    if used_poem_ids:
        query = query.where(Poem.id.notin_(used_poem_ids))
    query = query.order_by(Poem.recite_count.desc()).limit(1)
    poem_result = await db.execute(query)
    poem = poem_result.scalar_one_or_none()

    if not poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无可推荐的新诗词",
        )

    # 创建新推荐记录
    import uuid
    new_rec = DailyRecommendation(
        id=str(uuid.uuid4()),
        poem_id=poem.id,
        recommend_date=today,
        reason="根据您的偏好，为您推荐这首诗词",
        reason_type="manual",
    )
    db.add(new_rec)
    await db.commit()

    detail = await _poem_to_detail(db, poem, user_id)

    return DailySwitchResponse(
        poem=detail,
        reason="根据您的偏好，为您推荐这首诗词",
        reason_type="manual",
        can_switch=switch_count + 1 < 5,
        switch_count=switch_count + 1,
    )
