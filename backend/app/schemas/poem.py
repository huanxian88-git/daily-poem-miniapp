"""诗词相关 Schema"""

from pydantic import BaseModel


class PoemBrief(BaseModel):
    """诗词列表简要信息"""

    id: str
    title: str
    author: str | None = None
    dynasty: str | None = None
    difficulty: int
    tags: str | None = None  # 原始标签字符串
    first_line: str | None = None  # 首句（列表展示用）


class PoemDetail(BaseModel):
    """诗词详情"""

    id: str
    title: str
    author: str | None = None
    dynasty: str | None = None
    content: str
    content_lines: list[str] | None = None  # 从JSON解析
    annotation: str | None = None
    translation: str | None = None
    background: str | None = None
    difficulty: int
    tags: str | None = None
    tags_parsed: dict | None = None  # 解析后的标签 {imagery: [...], theme: [...], scene: [...]}
    scene_type: str | None = None
    scene_desc: str | None = None
    scene_image_url: str | None = None
    is_favorited: bool = False  # 当前用户是否已珍藏
    textbook_info: str | None = None  # 课本关联信息，如"人教版·七上·第2单元"


class PoemListResponse(BaseModel):
    poems: list[PoemBrief]
    total: int
    page: int
    page_size: int


class PoemSceneResponse(BaseModel):
    poem_id: str
    scene_type: str | None = None
    scene_desc: str | None = None
    scene_image_url: str | None = None
