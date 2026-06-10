"""珍藏 Schema"""

from pydantic import BaseModel

from app.schemas.poem import PoemBrief


class FavoriteResponse(BaseModel):
    is_favorited: bool
    poem_id: str


class FavoriteListResponse(BaseModel):
    poems: list[PoemBrief]
    total: int
