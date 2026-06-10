"""用户画像 Schema"""

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    age_group: str | None = None
    level: str | None = None
    interests: list[str] = []  # 从逗号分隔字符串解析
    recite_rhythm: str = "every_2_days"
    recite_rhythm_custom_days: int | None = None
    textbook_version: str | None = None
    textbook_grade: int | None = None
    textbook_semester: str | None = None
    is_student: bool = False


class ProfileUpdateRequest(BaseModel):
    age_group: str | None = None
    level: str | None = None
    interests: list[str] | None = None
    recite_rhythm: str | None = None
    recite_rhythm_custom_days: int | None = None
    textbook_version: str | None = None
    textbook_grade: int | None = None
    textbook_semester: str | None = None
    is_student: bool | None = None
