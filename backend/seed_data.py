"""种子数据入口脚本

用法：
    python seed_data.py
"""

import asyncio
from app.data.seed import seed_database

if __name__ == "__main__":
    asyncio.run(seed_database())
