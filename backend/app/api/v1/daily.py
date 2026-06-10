"""每日推荐 API：今日推荐 + 换一首 + 历史记录

阶段3升级：
- today/switch 端点使用 recommend_service 推荐规则引擎（而非简单DB查询）
- 新增 GET /history 端点支持分页查询历史推荐
"""

import json
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.poem import Poem
from app.models.recommendation import DailyRecommendation
from app.models.favorite import Favorite
from app.schemas.daily import DailyTodayResponse, DailySwitchResponse
from app.schemas.poem import PoemDetail
from app.services.recommend_service import get_daily_recommendation
from app.api.v1.poems import _parse_tags, _get_textbook_info

router = APIRouter()


class DailyHistoryItem(BaseModel):
    """历史推荐条目"""
    id: str
    date: date
    poem_id: str
    poem_title: str
    author: str | None = None
    dynasty: str | None = None
    reason: str | None = None
    reason_type: str | None = None


class DailyHistoryResponse(BaseModel):
    """历史推荐分页响应"""
    items: list[DailyHistoryItem]
    total: int
    page: int
    page_size: int


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
    """获取今日推荐诗词（使用推荐规则引擎）"""
    user_id = current_user.get("sub")
    today = date.today()

    # 优先查已有的置顶推荐或已生成推荐
    rec_result = await db.execute(
        select(DailyRecommendation)
        .where(DailyRecommendation.recommend_date == today)
        .order_by(DailyRecommendation.is_pinned.desc(), DailyRecommendation.created_at.desc())
        .limit(1)
    )
    existing_rec = rec_result.scalar_one_or_none()

    if existing_rec:
        # 已有推荐记录，直接返回
        poem_result = await db.execute(select(Poem).where(Poem.id == existing_rec.poem_id))
        poem = poem_result.scalar_one_or_none()
        if not poem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="推荐诗词不存在",
            )
        detail = await _poem_to_detail(db, poem, user_id)
        # 计算换诗次数
        count_result = await db.execute(
            select(DailyRecommendation).where(
                DailyRecommendation.recommend_date == today,
                DailyRecommendation.is_pinned == False,
            )
        )
        non_pinned_count = len(count_result.scalars().all())
        switch_count = max(0, non_pinned_count)

        return DailyTodayResponse(
            poem=detail,
            reason=existing_rec.reason or "今日为你推荐这首诗词",
            reason_type=existing_rec.reason_type,
            can_switch=switch_count < 5,
            switch_count=switch_count,
        )

    # 无已有推荐，使用推荐规则引擎
    poem, reason, reason_type = await get_daily_recommendation(
        db=db, today=today, user_id=user_id
    )

    if not poem:
        # 兜底：按背诵量排序取最热的一首
        poem_result = await db.execute(
            select(Poem).order_by(Poem.recite_count.desc()).limit(1)
        )
        poem = poem_result.scalar_one_or_none()
        if not poem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无诗词数据",
            )
        reason = "今日为你推荐这首经典名篇"
        reason_type = "manual"

    detail = await _poem_to_detail(db, poem, user_id)

    # 创建推荐记录（持久化）
    new_rec = DailyRecommendation(
        id=str(uuid.uuid4()),
        poem_id=poem.id,
        recommend_date=today,
        reason=reason,
        reason_type=reason_type,
        is_pinned=True,  # 首次推荐置顶
    )
    db.add(new_rec)
    await db.commit()

    return DailyTodayResponse(
        poem=detail,
        reason=reason,
        reason_type=reason_type,
        can_switch=True,
        switch_count=0,
    )


@router.post("/switch", response_model=DailySwitchResponse)
async def switch_daily_poem(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """换一首推荐诗词（使用推荐规则引擎）"""
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

    # 使用推荐规则引擎获取新推荐（排除已推荐的）
    poem, reason, reason_type = await get_daily_recommendation(
        db=db, today=today, user_id=user_id
    )

    if not poem:
        # 兜底随机
        used_result = await db.execute(
            select(DailyRecommendation).where(
                DailyRecommendation.recommend_date == today
            )
        )
        used_poem_ids = [r.poem_id for r in used_result.scalars().all()]
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
        reason = "根据您的偏好，为您推荐这首诗词"
        reason_type = "manual"

    # 创建新推荐记录
    new_rec = DailyRecommendation(
        id=str(uuid.uuid4()),
        poem_id=poem.id,
        recommend_date=today,
        reason=reason,
        reason_type=reason_type,
    )
    db.add(new_rec)
    await db.commit()

    detail = await _poem_to_detail(db, poem, user_id)

    return DailySwitchResponse(
        poem=detail,
        reason=reason,
        reason_type=reason_type,
        can_switch=switch_count + 1 < 5,
        switch_count=switch_count + 1,
    )

@router.get("/history", response_model=DailyHistoryResponse)
async def get_daily_history(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分页查询历史推荐记录"""
    # 总数
    total_result = await db.execute(
        select(func.count(DailyRecommendation.id))
    )
    total = total_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(DailyRecommendation)
        .order_by(DailyRecommendation.recommend_date.desc(), DailyRecommendation.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    records = result.scalars().all()

    items: list[DailyHistoryItem] = []
    for rec in records:
        poem_result = await db.execute(
            select(Poem.title, Poem.author, Poem.dynasty)
            .where(Poem.id == rec.poem_id)
        )
        poem_row = poem_result.first()
        items.append(DailyHistoryItem(
            id=rec.id,
            date=rec.recommend_date,
            poem_id=rec.poem_id,
            poem_title=poem_row[0] if poem_row else "未知",
            author=poem_row[1] if poem_row else None,
            dynasty=poem_row[2] if poem_row else None,
            reason=rec.reason,
            reason_type=rec.reason_type,
        ))

    return DailyHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
