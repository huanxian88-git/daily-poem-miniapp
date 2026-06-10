"""Redis 连接层：异步 Redis 客户端 + 缓存工具

支持 graceful degradation：Redis 不可用时自动降级为内存缓存，
不阻塞应用启动（适合开发环境）。
"""

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局 Redis 客户端实例
redis_client: Optional[aioredis.Redis] = None

# 内存降级缓存（Redis 不可用时使用）
_memory_cache: dict[str, Any] = {}
_redis_available: bool = False


async def init_redis() -> Optional[aioredis.Redis]:
    """初始化 Redis 连接池（含降级策略）"""
    global redis_client, _redis_available

    if not settings.REDIS_GRACEFUL_DEGRADATION:
        # 严格模式：必须连接成功
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        await redis_client.ping()
        _redis_available = True
        return redis_client

    # 降级模式：连接失败不阻塞
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        await redis_client.ping()
        _redis_available = True
        logger.info("Redis 连接成功")
    except Exception as e:
        _redis_available = False
        redis_client = None
        logger.warning(f"Redis 连接失败，已降级为内存缓存: {e}")

    return redis_client


async def close_redis() -> None:
    """关闭 Redis 连接"""
    global redis_client, _redis_available
    if redis_client:
        await redis_client.close()
        redis_client = None
        _redis_available = False


async def get_redis() -> Optional[aioredis.Redis]:
    """获取 Redis 客户端（依赖注入）"""
    global redis_client, _redis_available
    if redis_client is None and not _redis_available:
        await init_redis()
    return redis_client


def is_redis_available() -> bool:
    """Redis 是否可用"""
    return _redis_available


# --- 缓存工具函数（含内存降级） ---

async def cache_get(key: str) -> Optional[Any]:
    """从缓存读取（自动 JSON 反序列化）"""
    if _redis_available and redis_client:
        value = await redis_client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    else:
        # 内存降级
        return _memory_cache.get(key)


async def cache_set(key: str, value: Any, expire_seconds: int = 3600) -> None:
    """写入缓存（自动 JSON 序列化）"""
    if _redis_available and redis_client:
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, default=str)
        await redis_client.setex(key, expire_seconds, value)
    else:
        # 内存降级（忽略过期时间，开发够用）
        _memory_cache[key] = value


async def cache_delete(key: str) -> None:
    """删除缓存"""
    if _redis_available and redis_client:
        await redis_client.delete(key)
    else:
        _memory_cache.pop(key, None)


async def cache_exists(key: str) -> bool:
    """检查 key 是否存在"""
    if _redis_available and redis_client:
        return await redis_client.exists(key) > 0  # type: ignore
    else:
        return key in _memory_cache


# --- 业务专用缓存 ---

async def cache_today_recommendation(user_id: str, data: dict, expire: int = 86400) -> None:
    """缓存今日推荐结果"""
    key = f"daily_recommend:{user_id}"
    await cache_set(key, data, expire)


async def get_cached_today_recommendation(user_id: str) -> Optional[dict]:
    """获取缓存的今日推荐"""
    key = f"daily_recommend:{user_id}"
    return await cache_get(key)
