"""数据模型注册中心"""

from app.core.database import Base  # noqa: F401

# 导入所有模型以确保 SQLAlchemy 能发现它们创建表
from app.models.user import User, UserProfile  # noqa: F401
from app.models.poem import Poem  # noqa: F401
from app.models.recitation import Recitation  # noqa: F401
from app.models.review import ReviewSchedule  # noqa: F401
from app.models.favorite import Favorite  # noqa: F401
from app.models.event import Festival  # noqa: F401
from app.models.recommendation import DailyRecommendation  # noqa: F401
from app.models.textbook import Textbook, PoemTextbook  # noqa: F401
