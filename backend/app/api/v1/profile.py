"""用户画像 API：读取和更新用户画像数据"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter()


def _profile_to_response(profile: UserProfile) -> ProfileResponse:
    """将数据库模型转为响应对象"""
    interests = []
    if profile.interests:
        interests = [s.strip() for s in profile.interests.split(",") if s.strip()]
    return ProfileResponse(
        age_group=profile.age_group,
        level=profile.level,
        interests=interests,
        recite_rhythm=profile.recite_rhythm,
        recite_rhythm_custom_days=profile.recite_rhythm_custom_days,
        textbook_version=profile.textbook_version,
        textbook_grade=profile.textbook_grade,
        textbook_semester=profile.textbook_semester,
        is_student=profile.is_student,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户画像"""
    user_id = current_user.get("sub")
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户画像不存在",
        )
    return _profile_to_response(profile)


@router.put("", response_model=ProfileResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户画像"""
    user_id = current_user.get("sub")
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户画像不存在",
        )

    update_data = req.model_dump(exclude_none=True)
    if "interests" in update_data and update_data["interests"] is not None:
        update_data["interests"] = ",".join(update_data["interests"])

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return _profile_to_response(profile)


@router.post("", response_model=ProfileResponse)
async def create_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建用户画像（备用，通常login时已创建）"""
    user_id = current_user.get("sub")

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return _profile_to_response(existing)

    import uuid
    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return _profile_to_response(profile)
