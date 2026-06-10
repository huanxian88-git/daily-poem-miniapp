"""复习 API 路由：3个端点

全部需要 Bearer token 认证：
1. GET  /review/queue       → 今日复习队列
2. POST /review/{poem_id}/done → 标记复习完成
3. GET  /review/stats      → 复习统计摘要
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import review_service
from app.schemas.review import (
    ReviewQueueResponse,
    ReviewDoneRequest,
    ReviewDoneResponse,
    ReviewStatsResponse,
)

router = APIRouter()


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日复习队列（按紧急程度排序）"""
    user_id = current_user.get("sub")
    return await review_service.get_review_queue(db, user_id)


@router.post("/{poem_id}/done", response_model=ReviewDoneResponse)
async def mark_review_done(
    poem_id: str,
    body: ReviewDoneRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记复习完成并应用 SM-2 算法更新下次复习时间

    self_assessment:
    - easy: 简单（提高间隔）
    - good: 一般（正常增长）
    - hard: 困难（缩短间隔）
    """
    user_id = current_user.get("sub")
    try:
        return await review_service.mark_review_done(
            db=db,
            user_id=user_id,
            poem_id=poem_id,
            self_assessment=body.self_assessment,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取复习统计摘要（总数/已掌握/复习中/今日到期）"""
    user_id = current_user.get("sub")
    return await review_service.get_review_stats(db, user_id)
