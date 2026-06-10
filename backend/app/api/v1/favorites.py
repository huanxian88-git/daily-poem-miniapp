"""珍藏 API：添加/取消/列表"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.favorite import Favorite
from app.models.poem import Poem
from app.schemas.favorite import FavoriteResponse, FavoriteListResponse
from app.api.v1.poems import _get_first_line, _get_textbook_info
from app.schemas.poem import PoemBrief

router = APIRouter()


async def _poem_to_brief(db: AsyncSession, poem: Poem) -> PoemBrief:
    """将诗词模型转为简要信息"""
    return PoemBrief(
        id=poem.id,
        title=poem.title,
        author=poem.author,
        dynasty=poem.dynasty,
        difficulty=poem.difficulty,
        tags=poem.tags,
        first_line=_get_first_line(poem.content),
    )


@router.post("/{poem_id}", response_model=FavoriteResponse)
async def add_favorite(
    poem_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加珍藏"""
    user_id = current_user.get("sub")

    # 检查诗词是否存在
    poem_result = await db.execute(select(Poem).where(Poem.id == poem_id))
    if not poem_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诗词不存在",
        )

    # 检查是否已珍藏
    fav_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.poem_id == poem_id,
        )
    )
    existing = fav_result.scalar_one_or_none()
    if existing:
        return FavoriteResponse(is_favorited=True, poem_id=poem_id)

    # 创建珍藏记录
    import uuid
    favorite = Favorite(
        id=str(uuid.uuid4()),
        user_id=user_id,
        poem_id=poem_id,
    )
    db.add(favorite)
    await db.commit()

    return FavoriteResponse(is_favorited=True, poem_id=poem_id)


@router.delete("/{poem_id}", response_model=FavoriteResponse)
async def remove_favorite(
    poem_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消珍藏"""
    user_id = current_user.get("sub")

    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.poem_id == poem_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到珍藏记录",
        )

    await db.delete(favorite)
    await db.commit()

    return FavoriteResponse(is_favorited=False, poem_id=poem_id)


@router.get("", response_model=FavoriteListResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取珍藏列表"""
    user_id = current_user.get("sub")

    # 总数
    count_query = select(func.count()).select_from(Favorite).where(
        Favorite.user_id == user_id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询（JOIN Poem）
    offset = (page - 1) * page_size
    fav_query = (
        select(Favorite, Poem)
        .join(Poem, Favorite.poem_id == Poem.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(fav_query)
    rows = result.all()

    poems = []
    for fav, poem in rows:
        poems.append(await _poem_to_brief(db, poem))

    return FavoriteListResponse(poems=poems, total=total)
