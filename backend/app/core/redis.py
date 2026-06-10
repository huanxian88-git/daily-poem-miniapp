"""Redis 连接层：异步 Redis 客户端 + 缓存工具"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings


# 全局 Redis 客户端实例
redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    """初始化 Redis 连接池"""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    # 连接测试
    await redis_client.ping()
    return redis_client


async def close_redis() -> None:
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端（依赖注入）"""
    if redis_client is None:
        await init_redis()
    return redis_client  # type: ignore


# --- 缓存工具函数 ---

async def cache_get(key: str) -> Optional[Any]:
    """从缓存读取（自动 JSON 反序列化）"""
    client = await get_redis()
    value = await client.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


async def cache_set(key: str, value: Any, expire_seconds: int = 3600) -> None:
    """写入缓存（自动 JSON 序列化）"""
    client = await get_redis()
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, default=str)
    await client.setex(key, expire_seconds, value)


async def cache_delete(key: str) -> None:
    """删除缓存"""
    client = await get_redis()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    """检查 key 是否存在"""
    client = await get_redis()
    return await client.exists(key) > 0  # type: ignore


# --- 业务专用缓存 ---

async def cache_today_recommendation(user_id: str, data: dict, expire: int = 86400) -> None:
    """缓存今日推荐结果"""
    key = f"daily_recommend:{user_id}"
    await cache_set(key, data, expire)


async def get_cached_today_recommendation(user_id: str) -> Optional[dict]:
    """获取缓存的今日推荐"""
    key = f"daily_recommend:{user_id}"
    return await cache_get(key)


async def set_recite_lock(user_id: str, poem_id: str, expire: int = 3600) -> bool:
    """设置背诵守卫锁（最多同时背2首）"""
    client = await get_redis()
    lock_key = f"recite_lock:{user_id}"
    # 检查当前锁数量
    current = await client.llen(lock_key)
    if current >= 2:
        return False
    await client.rpush(lock_key, poem_id)
    await client.expire(lock_key, expire)
    return True


async def release_recite_lock(user_id: str, poem_id: str) -> None:
    """释放背诵守卫锁"""
    client = await get_redis()
    lock_key = f"recite_lock:{user_id}"
    await client.lrem(lock_key, 0, poem_id)
