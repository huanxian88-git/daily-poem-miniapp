"""数据导入脚本：从 JSON 文件批量导入诗词/诗词标签/日历事件"""

import asyncio
import json
import uuid
from pathlib import Path

from sqlalchemy import select, text

from app.core.database import async_session, engine
from app.models import Base
from app.models.poem import Poem, PoemTag
from app.models.event import CalendarEvent


DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "output"


async def init_db():
    """创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[seed] 数据库表创建完成")


async def import_poems():
    """导入诗词数据"""
    poems_file = DATA_DIR / "poems-all.json"
    if not poems_file.exists():
        print(f"[seed] 诗词文件不存在: {poems_file}")
        return

    with open(poems_file, "r", encoding="utf-8") as f:
        poems_data = json.load(f)

    async with async_session() as session:
        count = 0
        for item in poems_data:
            poem = Poem(
                id=uuid.UUID(item.get("id")) if item.get("id") else uuid.uuid4(),
                title=item.get("title", ""),
                author=item.get("author", ""),
                dynasty=item.get("dynasty", ""),
                content=item.get("content", ""),
                annotation=item.get("annotation"),
                translation=item.get("translation"),
                background=item.get("background"),
                difficulty=item.get("difficulty", 3),
                related_event=item.get("related_event"),
                textbook=item.get("textbook"),
                textbook_grade=item.get("textbook_grade"),
                scene_type=item.get("scene_type"),
                scene_desc=item.get("scene_desc"),
            )
            session.add(poem)

            # 解析标签字符串 "意象:月,意象:思乡|主题:羁旅|场景:月夜"
            tags_str = item.get("tags", "")
            if tags_str:
                for tag_part in tags_str.split("|"):
                    tag_part = tag_part.strip()
                    if ":" in tag_part:
                        cat, name = tag_part.split(":", 1)
                        cat = cat.strip()
                        name = name.strip()

                        # 映射类别
                        if cat == "意象":
                            category = "imagery"
                        elif cat == "主题":
                            category = "theme"
                        elif cat == "场景":
                            category = "scene"
                        else:
                            category = "scene"

                        tag = PoemTag(
                            poem_id=poem.id,
                            category=category,
                            name=name,
                            weight=1.0,
                        )
                        session.add(tag)

            count += 1
            if count % 50 == 0:
                await session.flush()
                print(f"[seed] 已导入 {count} 首诗词...")

        await session.commit()
        print(f"[seed] 诗词导入完成，共 {count} 首")


async def import_calendar():
    """导入日历事件"""
    calendar_file = DATA_DIR / "calendar_365.json"
    if not calendar_file.exists():
        print(f"[seed] 日历文件不存在: {calendar_file}")
        return

    with open(calendar_file, "r", encoding="utf-8") as f:
        calendar_data = json.load(f)

    async with async_session() as session:
        count = 0
        for item in calendar_data:
            event = CalendarEvent(
                id=uuid.uuid4(),
                event_date=item.get("event_date"),
                events=item.get("events"),
                season=item.get("season"),
                month=item.get("month", 1),
                day=item.get("day", 1),
            )
            session.add(event)
            count += 1

        await session.commit()
        print(f"[seed] 日历导入完成，共 {count} 天")


async def main():
    print("[seed] 开始数据导入...")
    await init_db()
    await import_poems()
    await import_calendar()
    print("[seed] 全部数据导入完成！")


if __name__ == "__main__":
    asyncio.run(main())
