"""
Redis 缓存服务 (旁路缓存模式)

特性:
- Redis 不可用时自动降级, 不影响业务
- 支持 JSON 序列化的 Python 对象
- 支持 TTL 过期
- 支持批量删除 (按前缀)
"""
import json
from typing import Any, Optional

from loguru import logger

from app.core.config import settings


class CacheService:
    """Redis 缓存服务 (带降级保护)"""

    def __init__(self) -> None:
        self._redis = None
        self._available = False
        self._init_redis()

    def _init_redis(self) -> None:
        """初始化 Redis 连接 (失败则降级)"""
        try:
            import redis
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            # 测试连接
            self._redis.ping()
            self._available = True
            logger.info("✅ Redis 缓存已连接")
        except Exception as e:
            self._available = False
            logger.warning(f"⚠️  Redis 不可用, 缓存降级: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def get(self, key: str) -> Optional[Any]:
        """获取缓存 (自动 JSON 反序列化)"""
        if not self._available:
            return None
        try:
            val = self._redis.get(key)
            if val is None:
                return None
            return json.loads(val)
        except Exception as e:
            logger.debug(f"缓存读取失败 {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存 (自动 JSON 序列化, ttl 单位秒)"""
        if not self._available:
            return False
        try:
            self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
            return True
        except Exception as e:
            logger.debug(f"缓存写入失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除单个缓存"""
        if not self._available:
            return False
        try:
            self._redis.delete(key)
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern: str) -> int:
        """按模式批量删除缓存 (返回删除数量)"""
        if not self._available:
            return 0
        try:
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
                return len(keys)
            return 0
        except Exception:
            return 0

    def get_or_set(self, key: str, factory, ttl: int = 300) -> Any:
        """获取缓存, 不存在则调用 factory 获取并缓存"""
        # 先查缓存
        cached = self.get(key)
        if cached is not None:
            return cached
        # 调用 factory 获取数据
        result = factory() if callable(factory) else factory
        # 写入缓存
        self.set(key, result, ttl)
        return result


# 全局单例
cache_service = CacheService()
