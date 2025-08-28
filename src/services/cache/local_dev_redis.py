"""Enhanced local development cache backend with Redis fallback"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from redis.asyncio import Redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from .base import CacheBackend

logger = logging.getLogger(__name__)

UTC = timezone.utc


class LocalDevRedisBackend(CacheBackend):
    """Enhanced local development cache backend with Redis fallback"""

    def __init__(
        self,
        backend_type: str = "elasticache",
        key_prefix: str = "mcp:",
        max_size: int = 1000,
        enable_persistence: bool = False,
        persistence_file: str = "local_cache.json",
        redis_url: str = "redis://localhost:6379",
        redis_password: str = "local_dev_password",
        fallback_to_memory: bool = True,
    ):
        """
        Initialize enhanced local development cache backend.

        Args:
            backend_type: Type to simulate ("elasticache", "dax")
            key_prefix: Prefix for all cache keys
            max_size: Maximum cache size for in-memory fallback
            enable_persistence: Enable persistence for in-memory fallback
            persistence_file: Persistence file path
            redis_url: Redis connection URL
            redis_password: Redis password
            fallback_to_memory: Whether to fallback to in-memory if Redis fails
        """
        self.backend_type = backend_type
        self.key_prefix = key_prefix
        self.max_size = max_size
        self.enable_persistence = enable_persistence
        self.persistence_file = persistence_file
        self.redis_url = redis_url
        self.redis_password = redis_password
        self.fallback_to_memory = fallback_to_memory

        # In-memory fallback
        self._cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()

        # Redis connection
        self._redis: Redis | None = None
        self._redis_available = False

        # Initialize Redis connection
        asyncio.create_task(self._init_redis())

        logger.info(f"Initialized enhanced local dev cache (type: {backend_type})")

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        return timedelta(minutes=15)  # Default 15 minutes TTL for local dev redis cache

    async def _init_redis(self) -> None:
        """Initialize Redis connection."""
        if not HAS_REDIS:
            logger.warning("Redis not available, using in-memory fallback")
            return

        try:
            # Parse Redis URL and add password
            if self.redis_url.startswith("redis://"):
                # Extract host and port
                url_parts = self.redis_url.replace("redis://", "").split("/")
                host_port = url_parts[0].split(":")
                host = host_port[0] if host_port[0] else "localhost"
                port = int(host_port[1]) if len(host_port) > 1 else 6379

                self._redis = Redis(
                    host=host,
                    port=port,
                    password=self.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )

                # Test connection
                if await self._redis.ping():
                    self._redis_available = True
                    logger.info(f"Redis connection established: {host}:{port}")
                else:
                    raise ConnectionError("Redis ping failed")

            else:
                raise ValueError(f"Invalid Redis URL: {self.redis_url}")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            if self.fallback_to_memory:
                logger.info("Falling back to in-memory cache")
            else:
                raise

    async def _make_key(self, key: str) -> str:
        """Make cache key with prefix."""
        return f"{self.key_prefix}{key}"

    async def _is_expired(self, item: dict[str, Any]) -> bool:
        """Check if cache item is expired."""
        if "expires_at" not in item:
            return False

        expires_at = datetime.fromisoformat(item["expires_at"]).replace(tzinfo=UTC)
        return datetime.now(UTC) > expires_at

    async def get(self, key: str) -> Any | None:
        """Get value from cache, trying Redis first, then in-memory."""
        prefixed_key = await self._make_key(key)

        # Try Redis first
        if self._redis_available and self._redis:
            try:
                value = await self._redis.get(prefixed_key)
                if value is not None:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
                self._redis_available = False

        # Fallback to in-memory
        async with self._lock:
            if prefixed_key not in self._cache:
                return None

            item = self._cache[prefixed_key]

            # Check if expired
            if await self._is_expired(item):
                del self._cache[prefixed_key]
                return None

            # Update last accessed
            item["last_accessed"] = datetime.now(UTC).isoformat()
            return item["value"]

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache, writing to both Redis and in-memory."""
        prefixed_key = await self._make_key(key)

        # Prepare data
        now = datetime.now(UTC)
        item_data = {
            "value": value,
            "created_at": now.isoformat(),
            "last_accessed": now.isoformat(),
        }

        if ttl:
            expires_at = now + ttl
            item_data["expires_at"] = expires_at.isoformat()

        # Try Redis first
        if self._redis_available and self._redis:
            try:
                redis_value = json.dumps(value)
                if ttl:
                    await self._redis.setex(
                        prefixed_key, int(ttl.total_seconds()), redis_value
                    )
                else:
                    await self._redis.set(prefixed_key, redis_value)
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
                self._redis_available = False

        # Always write to in-memory as backup
        async with self._lock:
            self._cache[prefixed_key] = item_data

            # Cleanup and enforce limits
            await self._cleanup_expired()
            await self._enforce_max_size()

            # Save persistence if enabled
            if self.enable_persistence:
                await self._save_persistence()

        logger.debug(f"Cached key {key} with TTL {ttl}")
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache from both Redis and in-memory."""
        prefixed_key = await self._make_key(key)

        # Try Redis first
        if self._redis_available and self._redis:
            try:
                await self._redis.delete(prefixed_key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
                self._redis_available = False

        # Delete from in-memory
        async with self._lock:
            if prefixed_key in self._cache:
                del self._cache[prefixed_key]

                # Save persistence if enabled
                if self.enable_persistence:
                    await self._save_persistence()

                logger.debug(f"Deleted cache key {key}")
                return True

        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        prefixed_key = await self._make_key(key)

        # Try Redis first
        if self._redis_available and self._redis:
            try:
                return bool(await self._redis.exists(prefixed_key))
            except Exception as e:
                logger.warning(f"Redis exists failed: {e}")
                self._redis_available = False

        # Check in-memory
        async with self._lock:
            if prefixed_key not in self._cache:
                return False

            # Check if expired
            if await self._is_expired(self._cache[prefixed_key]):
                del self._cache[prefixed_key]
                return False

            return True

    async def clear(self) -> bool:
        """Clear all cached data from both Redis and in-memory."""
        # Try Redis first
        if self._redis_available and self._redis:
            try:
                # Get all keys with prefix and delete them
                pattern = f"{self.key_prefix}*"
                keys = await self._redis.keys(pattern)
                if keys:
                    await self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")
                self._redis_available = False

        # Clear in-memory
        async with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()

            # Save persistence if enabled
            if self.enable_persistence:
                await self._save_persistence()

            logger.info(f"Cleared {cleared_count} cache items")
            return True

    async def close(self) -> None:
        """Close cache backend and save persistence."""
        # Close Redis connection
        if self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

        # Save persistence if enabled
        async with self._lock:
            if self.enable_persistence:
                await self._save_persistence()

        logger.debug("Closed enhanced local dev cache backend")

    async def ping(self) -> bool:
        """Check if cache is available."""
        # Try Redis first
        if self._redis_available and self._redis:
            try:
                return await self._redis.ping()
            except Exception as e:
                logger.warning(f"Redis ping failed: {e}")
                self._redis_available = False

        # Fallback to in-memory
        return True

    async def get_cluster_health(self) -> dict[str, Any]:
        """Get simulated cluster health information."""
        # Try Redis first
        redis_health = None
        if self._redis_available and self._redis:
            try:
                info = await self._redis.info()
                redis_health = {
                    "status": "healthy",
                    "cluster_status": "available",
                    "backend_type": f"redis_{self.backend_type}",
                    "node_count": 1,
                    "node_statuses": ["available"],
                    "endpoint": self.redis_url,
                    "region": "local",
                    "redis_info": {
                        "version": info.get("redis_version", "unknown"),
                        "used_memory_human": info.get("used_memory_human", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "total_commands_processed": info.get(
                            "total_commands_processed", 0
                        ),
                    },
                }
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                self._redis_available = False

        # In-memory fallback health
        async with self._lock:
            total_items = len(self._cache)
            expired_items = 0
            active_items = 0

            for item in self._cache.values():
                if await self._is_expired(item):
                    expired_items += 1
                else:
                    active_items += 1

            memory_health = {
                "status": "healthy" if self._redis_available else "degraded",
                "cluster_status": "available",
                "backend_type": f"local_{self.backend_type}",
                "node_count": 1,
                "node_statuses": ["available"],
                "endpoint": "localhost",
                "region": "local",
                "cache_stats": {
                    "total_items": total_items,
                    "active_items": active_items,
                    "expired_items": expired_items,
                    "max_size": self.max_size,
                    "utilization_percent": (
                        (total_items / self.max_size) * 100 if self.max_size > 0 else 0
                    ),
                },
            }

        # Return Redis health if available, otherwise memory health
        if redis_health:
            return redis_health
        return memory_health

    def get_stats(self) -> dict[str, Any]:
        """Get detailed cache statistics."""
        # In-memory stats
        total_items = len(self._cache)
        expired_items = 0
        active_items = 0
        total_size_bytes = 0

        for item in self._cache.values():
            if self._is_expired(item):
                expired_items += 1
            else:
                active_items += 1
                # Estimate size
                try:
                    item_size = len(json.dumps(item["value"]))
                    total_size_bytes += item_size
                except (TypeError, ValueError):
                    total_size_bytes += 100

        return {
            "total_items": total_items,
            "active_items": active_items,
            "expired_items": expired_items,
            "max_size": self.max_size,
            "utilization_percent": (
                (total_items / self.max_size) * 100 if self.max_size > 0 else 0
            ),
            "total_size_bytes": total_size_bytes,
            "total_size_mb": total_size_bytes / (1024 * 1024),
            "backend_type": self.backend_type,
            "persistence_enabled": self.enable_persistence,
            "key_prefix": self.key_prefix,
            "redis_available": self._redis_available,
            "redis_url": self.redis_url,
        }

    async def _cleanup_expired(self) -> None:
        """Clean up expired items from in-memory cache."""
        expired_keys = []
        for key, item in self._cache.items():
            if await self._is_expired(item):
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired items")

    async def _enforce_max_size(self) -> None:
        """Enforce maximum cache size for in-memory cache."""
        if len(self._cache) <= self.max_size:
            return

        # Remove oldest items (LRU-like)
        items_to_remove = len(self._cache) - self.max_size
        sorted_items = sorted(
            self._cache.items(), key=lambda x: x[1].get("last_accessed", "0")
        )

        for i in range(items_to_remove):
            del self._cache[sorted_items[i][0]]

        logger.debug(f"Removed {items_to_remove} items to enforce max size")

    async def _save_persistence(self) -> None:
        """Save in-memory cache to disk."""
        if not self.enable_persistence:
            return

        try:
            data = {
                "cache": self._cache,
                "metadata": {
                    "saved_at": datetime.now(UTC).isoformat(),
                    "backend_type": self.backend_type,
                    "key_prefix": self.key_prefix,
                },
            }

            with open(self.persistence_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save persistence: {e}")

    async def _load_persistence(self) -> None:
        """Load in-memory cache from disk."""
        if not self.enable_persistence:
            return

        try:
            with open(self.persistence_file) as f:
                data = json.load(f)
                self._cache = data.get("cache", {})

        except FileNotFoundError:
            logger.debug("No persistence file found, starting with empty cache")
        except Exception as e:
            logger.error(f"Failed to load persistence: {e}")

    def get_redis_status(self) -> dict[str, Any]:
        """Get Redis connection status."""
        return {
            "redis_available": self._redis_available,
            "redis_url": self.redis_url,
            "fallback_to_memory": self.fallback_to_memory,
            "current_backend": "redis" if self._redis_available else "memory",
        }
