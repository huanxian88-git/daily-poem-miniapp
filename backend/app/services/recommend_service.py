"""每日推荐服务层 — 推荐规则引擎

推荐优先级（从高到低）：
1. 节日匹配：根据当天日期匹配 Festival → 通过 poem_tags 匹配 Poem
2. 课本匹配：根据用户绑定的课本版本匹配 PoemTextbook → Poem
3. 标签匹配：根据用户偏好标签匹配 Poem.tags
4. 随机兜底：从未推荐过的诗词中随机选一首

阶段3使用模板生成推荐理由，阶段5将接入混元大模型。
"""

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poem import Poem
from app.models.event import Festival
from app.models.recommendation import DailyRecommendation
from app.models.textbook import PoemTextbook
from app.models.user import UserProfile


# ---- 推荐理由模板 ----
_REASON_TEMPLATES = {
    "festival": "{festival_name}将至，这首{poem_title}恰应时节，值得品读。",
    "solar_term": "今日{festival_name}，推荐您读这首应景佳作——{poem_title}。",
    "textbook": "这是您课本({textbook_name})里的必背篇目，今天来学习吧！",
    "tag_match": "根据您的阅读偏好，为您精选了这首{poem_title}。",
    "random": "今日为您推荐经典名篇——{poem_title}。",
}

# ---- 标签匹配辅助函数 ----

def _tags_match(poem_tags: Optional[str], target_tags: Optional[str]) -> bool:
    """判断两个标签字符串是否有交集。

    标签格式："意象:月,意象:春雨|主题:思乡"
    使用 '|' 分割顶层类别，',' 分割同类别标签。

    Args:
        poem_tags: 诗词标签字符串
        target_tags: 目标标签字符串（如节日关联的poem_tags）

    Returns:
        是否有交集
    """
    if not poem_tags or not target_tags:
        return False

    # 提取单个标签token
    def extract_tags(tag_str: str) -> set[str]:
        tokens: set[str] = set()
        for part in tag_str.split("|"):
            part = part.strip()
            if not part:
                continue
            for item in part.split(","):
                item = item.strip()
                if item:
                    tokens.add(item)
        return tokens

    poem_tag_set = extract_tags(poem_tags)
    target_tag_set = extract_tags(target_tags)

    return bool(poem_tag_set & target_tag_set)


async def get_daily_recommendation(
    db: AsyncSession,
    today: date,
    user_id: Optional[str] = None,
) -> tuple[Optional[Poem], str, str]:
    """每日推荐规则引擎。

    按优先级依次尝试各推荐策略，返回第一个命中的结果。

    Args:
        db: 数据库会话
        today: 目标日期
        user_id: 用户ID（可选，用于课本匹配）

    Returns:
        (推荐的诗词, 推荐理由, 推荐类型)
        如果没有可推荐的诗词，返回 (None, "", "")
    """
    # 获取今日已推荐过的诗词ID集合
    used_result = await db.execute(
        select(DailyRecommendation.poem_id).where(
            DailyRecommendation.recommend_date == today
        )
    )
    used_poem_ids: set[str] = set(r[0] for r in used_result.all())

    # ---- 策略1：节日匹配 ----
    festival_poem = await _match_festival(db, today, used_poem_ids)
    if festival_poem:
        reason = _build_reason("festival", poem_title=festival_poem.title)
        return festival_poem, reason, "festival"

    # ---- 策略2：课本匹配 ----
    if user_id:
        textbook_poem, textbook_name = await _match_textbook(
            db, user_id, used_poem_ids
        )
        if textbook_poem:
            reason = _build_reason(
                "textbook",
                poem_title=textbook_poem.title,
                textbook_name=textbook_name or "教材",
            )
            return textbook_poem, reason, "textbook"

    # ---- 策略3：标签匹配（随机选一首有标签的） ----
    tag_poem = await _match_random_with_tags(db, used_poem_ids)
    if tag_poem:
        reason = _build_reason("tag_match", poem_title=tag_poem.title)
        return tag_poem, reason, "tag_match"

    # ---- 策略4：纯随机兜底 ----
    random_poem = await _match_fallback_random(db, used_poem_ids)
    if random_poem:
        reason = _build_reason("random", poem_title=random_poem.title)
        return random_poem, reason, "manual"

    return None, "", ""


# ---- 各策略实现 ----

async def _match_festival(
    db: AsyncSession,
    today: date,
    exclude_ids: set[str],
) -> Optional[Poem]:
    """策略1：根据日期匹配节日/节气。

    匹配逻辑：
    1. 查询 Festival 表中 date_rule 匹配今天的记录
    2. 取其 poem_tags
    3. 在 Poem 表中找 tags 有交集且不在排除列表中的诗词

    Args:
        db: 数据库会话
        today: 今天日期
        exclude_ids: 已排除的诗词ID集合

    Returns:
        命中的诗词或 None
    """
    # 查询匹配的节日
    festivals_result = await db.execute(select(Festival))
    all_festivals = festivals_result.scalars().all()

    matched_festival: Optional[Festival] = None
    for f in all_festivals:
        if _match_date_rule(f.date_rule, today):
            matched_festival = f
            break

    if not matched_festival or not matched_festival.poem_tags:
        return None

    # 在Poem表中查找有标签交集的
    poems_result = await db.execute(
        select(Poem).where(
            Poem.status == "active",
            Poem.id.notin_(exclude_ids) if exclude_ids else True,
        ).order_by(Poem.recite_count.desc())
    )
    poems = poems_result.scalars().all()

    for poem in poems:
        if _tags_match(poem.tags, matched_festival.poem_tags):
            return poem

    return None


async def _match_textbook(
    db: AsyncSession,
    user_id: str,
    exclude_ids: set[str],
) -> tuple[Optional[Poem], Optional[str]]:
    """策略2：根据用户绑定的课本匹配诗词。

    Args:
        db: 数据库会话
        user_id: 用户ID
        exclude_ids: 已排除的诗词ID集合

    Returns:
        (命中的诗词, 课本名称) 或 (None, None)
    """
    # 查询用户画像
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile or not profile.textbook_version:
        return None, None

    # 查询该课本关联的诗词
    from sqlalchemy import func as sa_func

    query = (
        select(Poem)
        .join(PoemTextbook, PoemTextbook.poem_id == Poem.id)
        .where(Poem.status == "active")
    )
    if exclude_ids:
        query = query.where(Poem.id.notin_(exclude_ids))
    query = query.order_by(sa_func.random()).limit(1)

    poem_result = await db.execute(query)
    poem = poem_result.scalar_one_or_none()

    return poem, profile.textbook_version


async def _match_random_with_tags(
    db: AsyncSession,
    exclude_ids: set[str],
) -> Optional[Poem]:
    """策略3：从带标签的诗词中随机选一首未推荐过的。

    Args:
        db: 数据库会话
        exclude_ids: 已排除的诗词ID集合

    Returns:
        诗词或 None
    """
    from sqlalchemy import func as sa_func

    query = select(Poem).where(
        Poem.status == "active",
        Poem.tags.isnot(None),
        Poem.tags != "",
    )
    if exclude_ids:
        query = query.where(Poem.id.notin_(exclude_ids))
    query = query.order_by(sa_func.random()).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _match_fallback_random(
    db: AsyncSession,
    exclude_ids: set[str],
) -> Optional[Poem]:
    """策略4：纯随机兜底，从所有活跃诗词中选一首未推荐过的。

    Args:
        db: 数据库会话
        exclude_ids: 已排除的诗词ID集合

    Returns:
        诗词或 None
    """
    from sqlalchemy import func as sa_func

    query = select(Poem).where(Poem.status == "active")
    if exclude_ids:
        query = query.where(Poem.id.notin_(exclude_ids))
    query = query.order_by(sa_func.random()).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


# ---- 辅助函数 ----

def _match_date_rule(date_rule: str, target_date: date) -> bool:
    """判断日期规则是否匹配目标日期。

    支持格式：
    - G:MM-DD  公历日期（如 G:03-21 表示3月21日）
    - L:MM-DD  农历日期（阶段3仅支持公历，农历暂返回False）
    - S:名称   节气名（如 S:清明，阶段3简化处理）

    Args:
        date_rule: 日期规则字符串
        target_date: 目标日期

    Returns:
        是否匹配
    """
    if not date_rule:
        return False

    parts = date_rule.split(":", 1)
    if len(parts) != 2:
        return False

    rule_type, rule_value = parts[0].strip(), parts[1].strip()

    if rule_type == "G":
        # 公历 MM-DD 匹配
        try:
            month_day = rule_value.split("-")
            if len(month_day) == 2:
                m, d = int(month_day[0]), int(month_day[1])
                return target_date.month == m and target_date.day == d
        except (ValueError, IndexError):
            pass

    elif rule_type == "S":
        # 节气匹配（阶段3简化：近似日期映射+容差）
        solar_term_dates = {
            "立春": (2, 3, 5), "雨水": (2, 18, 5),
            "惊蛰": (3, 5, 5), "春分": (3, 20, 5),
            "清明": (4, 4, 5), "谷雨": (4, 19, 5),
            "立夏": (5, 5, 5), "小满": (5, 20, 5),
            "芒种": (6, 5, 5), "夏至": (6, 21, 5),
            "小暑": (7, 6, 5), "大暑": (7, 22, 5),
            "立秋": (8, 7, 5), "处暑": (8, 22, 5),
            "白露": (9, 7, 5), "秋分": (9, 22, 5),
            "寒露": (10, 8, 5), "霜降": (10, 23, 5),
            "立冬": (11, 7, 5), "小雪": (11, 22, 5),
            "大雪": (12, 6, 5), "冬至": (12, 21, 5),
            "小寒": (1, 5, 5), "大寒": (1, 20, 5),
        }
        if rule_value in solar_term_dates:
            m, d, tolerance = solar_term_dates[rule_value]
            try:
                diff = abs(target_date - date(target_date.year, m, d)).days
                return diff <= tolerance
            except (ValueError, AttributeError):
                return False

    # L: 农历（阶段3不支持）
    return False


def _build_reason(
    reason_type: str,
    **kwargs: str,
) -> str:
    """根据模板构建推荐理由。

    Args:
        reason_type: 理由类型
        **kwargs: 模板变量

    Returns:
        格式化后的理由文本
    """
    template = _REASON_TEMPLATES.get(reason_type, _REASON_TEMPLATES["random"])
    try:
        return template.format(**kwargs)
    except KeyError:
        return template.format(poem_title="这首诗词")
