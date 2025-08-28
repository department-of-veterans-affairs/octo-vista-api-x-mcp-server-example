"""Redis cache implementation for production use"""

import json
import logging
from datetime import timedelta
from typing import Any

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    Redis = None  # type: ignore[assignment, misc]

from .base import CacheBackend

logger = logging.getLogger(__name__)


class RedisCacheBackend(CacheBackend):
    """Redis-based cache backend for production use"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "mcp:",
        connection_pool_kwargs: dict[str, Any] | None = None,
    ):
        """
        Initialize Redis cache backend.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all keys
            connection_pool_kwargs: Additional connection pool arguments
        """
        if not HAS_REDIS:
            raise ImportError(
                "Redis support not installed. Install with: pip install redis[hiredis]"
            )

        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis: Redis | None = None
        self._connection_pool_kwargs = connection_pool_kwargs or {}

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        return timedelta(hours=1)  # Default 1 hour TTL for Redis

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            # Configure connection pool for Redis
            pool_kwargs = {
                "max_connections": 10,
                "retry_on_timeout": True,
                "health_check_interval": 30,
                **self._connection_pool_kwargs,
            }

            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                **pool_kwargs,
            )

        if self._redis is None:
            raise RuntimeError("Failed to initialize Redis client")

        return self._redis

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            value = await redis_client.get(prefixed_key)
            if value is None:
                return None

            # Decode JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode cached value for key {key}")
                # Remove corrupted data
                await self.delete(key)
                return None

        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            # Encode to JSON
            try:
                json_value = json.dumps(value)
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to encode value for key {key}: {e}")
                return False

            # Set with optional TTL
            if ttl:
                ttl_seconds = int(ttl.total_seconds())
                await redis_client.setex(prefixed_key, ttl_seconds, json_value)
            else:
                await redis_client.set(prefixed_key, json_value)

            logger.debug(f"Cached key {key} with TTL {ttl}")
            return True

        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            result = await redis_client.delete(prefixed_key)
            return result > 0

        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            return await redis_client.exists(prefixed_key) > 0

        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cached data with our prefix."""
        try:
            redis_client = await self._get_redis()

            # Use SCAN to find all keys with our prefix
            cursor = 0
            pattern = f"{self.key_prefix}*"

            while True:
                cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)

                if keys:
                    await redis_client.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Cleared all cache keys with prefix {self.key_prefix}")
            return True

        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.debug("Closed Redis connection")

    async def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            redis_client = await self._get_redis()
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
