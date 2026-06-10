"""诗词内容 API：列表/详情/场景"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.poem import Poem
from app.models.favorite import Favorite
from app.models.textbook import PoemTextbook, Textbook
from app.schemas.poem import (
    PoemBrief,
    PoemDetail,
    PoemListResponse,
    PoemSceneResponse,
)

router = APIRouter()


def _parse_tags(tags_str: str | None) -> dict:
    """解析 tags 字符串为结构化字典

    输入格式: "意象:月,意象:春雨|主题:思乡|场景:清明"
    输出格式: {"imagery": ["月", "春雨"], "theme": ["思乡"], "scene": ["清明"]}
    """
    if not tags_str:
        return {}
    result = {}
    for group in tags_str.split("|"):
        group = group.strip()
        if not group:
            continue
        for item in group.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                key, value = item.split(":", 1)
                key = key.strip()
                value = value.strip()
                # 映射中文类别到英文键名
                key_map = {
                    "意象": "imagery",
                    "主题": "theme",
                    "场景": "scene",
                }
                mapped_key = key_map.get(key, key)
                if mapped_key not in result:
                    result[mapped_key] = []
                result[mapped_key].append(value)
    return result


def _get_first_line(content: str) -> str | None:
    """提取首句"""
    if not content:
        return None
    # 按标点分割取第一句
    for sep in ["。", "？", "！", "\n"]:
        idx = content.find(sep)
        if idx > 0:
            return content[:idx + 1]
    return content[:12] + ("…" if len(content) > 12 else "")


async def _get_textbook_info(db: AsyncSession, poem_id: str) -> str | None:
    """获取课本关联信息"""
    result = await db.execute(
        select(PoemTextbook, Textbook)
        .join(Textbook, PoemTextbook.textbook_id == Textbook.id)
        .where(PoemTextbook.poem_id == poem_id)
        .limit(1)
    )
    row = result.one_or_none()
    if not row:
        return None
    pt, tb = row
    grade_name = {7: "七", 8: "八", 9: "九"}.get(pt.grade, str(pt.grade))
    sem_name = "上" if pt.semester == "upper" else "下"
    unit_info = f"第{pt.unit}单元" if pt.unit else ""
    return f"{tb.name}·{grade_name}年级{sem_name}册{('·' + unit_info) if unit_info else ''}"


@router.get("", response_model=PoemListResponse)
async def list_poems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="标题/作者模糊搜索"),
    difficulty: int | None = Query(None, ge=1, le=3, description="难度筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分页获取诗词列表"""
    query = select(Poem)

    # 搜索过滤
    if search:
        query = query.where(
            or_(
                Poem.title.contains(search),
                Poem.author.contains(search),
            )
        )

    # 难度过滤
    if difficulty is not None:
        query = query.where(Poem.difficulty == difficulty)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(Poem.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    poems = result.scalars().all()

    poem_briefs = [
        PoemBrief(
            id=p.id,
            title=p.title,
            author=p.author,
            dynasty=p.dynasty,
            difficulty=p.difficulty,
            tags=p.tags,
            first_line=_get_first_line(p.content),
        )
        for p in poems
    ]

    return PoemListResponse(
        poems=poem_briefs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{poem_id}", response_model=PoemDetail)
async def get_poem_detail(
    poem_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取诗词详情"""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = result.scalar_one_or_none()
    if not poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诗词不存在",
        )

    # 解析 content_lines
    content_lines = None
    if poem.content_lines:
        try:
            content_lines = json.loads(poem.content_lines)
        except (json.JSONDecodeError, TypeError):
            pass

    # 检查是否已珍藏
    user_id = current_user.get("sub")
    fav_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.poem_id == poem_id,
        )
    )
    is_favorited = fav_result.scalar_one_or_none() is not None

    # 课本关联信息
    textbook_info = await _get_textbook_info(db, poem_id)

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


@router.get("/{poem_id}/scene", response_model=PoemSceneResponse)
async def get_poem_scene(
    poem_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取诗词AI联想场景（阶段2返回数据或模板生成）"""
    result = await db.execute(select(Poem).where(Poem.id == poem_id))
    poem = result.scalar_one_or_none()
    if not poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诗词不存在",
        )

    scene_desc = poem.scene_desc
    # 如果数据库中没有场景描述，用模板生成
    if not scene_desc:
        dynasty_text = f"{poem.dynasty}时期" if poem.dynasty else "古代"
        author_text = f"，诗人{poem.author}" if poem.author else ""
        scene_desc = f"{dynasty_text}{author_text}，{poem.title}的意境深远。"

    return PoemSceneResponse(
        poem_id=poem.id,
        scene_type=poem.scene_type,
        scene_desc=scene_desc,
        scene_image_url=poem.scene_image_url,
    )
