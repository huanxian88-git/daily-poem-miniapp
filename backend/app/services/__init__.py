"""服务层模块注册"""

# 背诵服务
from app.services.recite_service import (  # noqa: F401
    start_recite,
    fill_check,
    sort_check,
    voice_check,
    check_mastery,
    abandon_recite,
    get_recite_list,
    get_recite_result,
)

# 复习服务
from app.services.review_service import (  # noqa: F401
    get_review_queue,
    mark_review_done,
    get_review_stats,
)

# 推荐服务
from app.services.recommend_service import (  # noqa: F401
    get_daily_recommendation,
)
