"""背诵 API 路由：7个端点

全部需要 Bearer token 认证：
1. GET  /recite/list          → 在背列表
2. POST /recite/start         → 开始背诵
3. POST /recite/{id}/fill     → 补阙填词检查
4. POST /recite/{id}/sort     → 排序归位检查
5. POST /recite/{id}/voice    → 语音背诵检查（阶段3 mock）
6. GET  /recite/{id}/result   → 背诵结果总览
7. POST /recite/{id}/abandon  → 放弃背诵
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import recite_service
from app.schemas.recitation import (
    RecitationStartRequest,
    RecitationStartResponse,
    FillCheckRequest,
    FillCheckResponse,
    SortCheckRequest,
    SortCheckResponse,
    VoiceCheckResponse,
    RecitationResultResponse,
    RecitationListResponse,
)

router = APIRouter()


@router.get("/list", response_model=RecitationListResponse)
async def get_recite_list(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前在背列表"""
    user_id = current_user.get("sub")
    return await recite_service.get_recite_list(db, user_id)


@router.post("/start", response_model=RecitationStartResponse)
async def start_recite(
    body: RecitationStartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """开始背诵一首诗词"""
    user_id = current_user.get("sub")
    try:
        return await recite_service.start_recite(
            db=db,
            user_id=user_id,
            poem_id=body.poem_id,
            confirmed=body.confirmed,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{recitation_id}/fill", response_model=FillCheckResponse)
async def fill_check(
    recitation_id: str,
    body: FillCheckRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """补阙填词关卡检查"""
    try:
        return await recite_service.fill_check(
            db=db,
            recitation_id=recitation_id,
            answers=body.answers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{recitation_id}/sort", response_model=SortCheckResponse)
async def sort_check(
    recitation_id: str,
    body: SortCheckRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """排序归位关卡检查"""
    try:
        return await recite_service.sort_check(
            db=db,
            recitation_id=recitation_id,
            order=body.order,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{recitation_id}/voice", response_model=VoiceCheckResponse)
async def voice_check(
    recitation_id: str,
    body: dict,  # {"recognized_text": "..."}
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """语音背诵关卡检查（阶段3 mock 版，直接接受 recognized_text）"""
    recognized_text = body.get("recognized_text", "")
    if not recognized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少 recognized_text 参数",
        )

    try:
        return await recite_service.voice_check(
            db=db,
            recitation_id=recitation_id,
            recognized_text=recognized_text,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{recitation_id}/result", response_model=RecitationResultResponse)
async def get_recite_result(
    recitation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取背诵完整结果（三关总览+是否掌握）"""
    try:
        return await recite_service.get_recite_result(db, recitation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{recitation_id}/abandon", status_code=status.HTTP_204_NO_CONTENT)
async def abandon_recite(
    recitation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """放弃当前背诵（删除记录）"""
    try:
        await recite_service.abandon_recite(db, recitation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
