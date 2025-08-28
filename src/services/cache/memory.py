"""In-memory cache implementation for development/testing"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from .base import CacheBackend

logger = logging.getLogger(__name__)


class MemoryCacheBackend(CacheBackend):
    """Simple in-memory cache backend using dict"""

    def __init__(self):
        """Initialize memory cache."""
        self._cache: dict[str, tuple[Any, datetime | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check expiry
            if expiry and datetime.now(UTC) > expiry:
                # Expired, remove it
                del self._cache[key]
                logger.debug(f"Cache key {key} expired")
                return None

            logger.debug(f"Cache hit for key {key}")
            return value

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache."""
        async with self._lock:
            expiry = None
            if ttl:
                expiry = datetime.now(UTC) + ttl

            self._cache[key] = (value, expiry)
            logger.debug(f"Cached key {key} with TTL {ttl}")
            return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache key {key}")
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        async with self._lock:
            if key not in self._cache:
                return False

            # Check if expired
            value, expiry = self._cache[key]
            if expiry and datetime.now(UTC) > expiry:
                # Expired, remove it
                del self._cache[key]
                return False

            return True

    async def clear(self) -> bool:
        """Clear all cached data."""
        async with self._lock:
            self._cache.clear()
            logger.debug("Cleared all cache entries")
            return True

    async def close(self) -> None:
        """No cleanup needed for memory cache."""
        pass

    async def ping(self) -> bool:
        """Check if cache is available."""
        return True

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        return timedelta(minutes=5)  # Default 5 minutes TTL for memory cache

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics (for debugging)."""
        total_keys = len(self._cache)
        expired_keys = 0
        now = datetime.now(UTC)

        for _, (_, expiry) in self._cache.items():
            if expiry and now > expiry:
                expired_keys += 1

        return {
            "total_keys": total_keys,
            "active_keys": total_keys - expired_keys,
            "expired_keys": expired_keys,
        }
