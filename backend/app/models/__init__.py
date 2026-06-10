"""数据模型注册中心"""

from app.core.database import Base  # noqa: F401

# 在此导入所有模型以确保 Alembic 能发现它们
from app.models.user import User, UserProfile  # noqa: F401
from app.models.poem import Poem, PoemTag  # noqa: F401
from app.models.recitation import Recitation, RecitationStep  # noqa: F401
from app.models.review import ReviewSchedule  # noqa: F401
from app.models.favorite import Favorite  # noqa: F401
from app.models.event import Festival, CalendarEvent  # noqa: F401
from app.models.recommendation import DailyRecommendation  # noqa: F401
