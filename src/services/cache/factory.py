"""Factory for creating cache backends"""

import logging
import os
from datetime import timedelta

from .base import CacheBackend, PatientDataCache
from .memory import MemoryCacheBackend
from .redis import RedisCacheBackend

logger = logging.getLogger(__name__)


class CacheFactory:
    """Factory for creating cache backends"""

    @staticmethod
    async def create_backend() -> CacheBackend:
        """
        Create cache backend based on environment configuration.

        Environment variables:
            CACHE_BACKEND: "redis" or "memory" (default: "memory")
            REDIS_URL: Redis connection URL (default: "redis://localhost:6379/0")
            CACHE_KEY_PREFIX: Prefix for all cache keys (default: "mcp:")

        Returns:
            Cache backend instance
        """
        backend_type = os.getenv("CACHE_BACKEND", "memory").lower()

        if backend_type == "redis":
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            key_prefix = os.getenv("CACHE_KEY_PREFIX", "mcp:")

            try:
                backend = RedisCacheBackend(redis_url=redis_url, key_prefix=key_prefix)
                # Test connection
                if await backend.ping():
                    logger.info(f"Created Redis cache backend with URL: {redis_url}")
                    return backend
                else:
                    logger.warning("Redis ping failed. Falling back to memory cache.")
                    return MemoryCacheBackend()
            except ImportError as e:
                logger.warning(
                    f"Redis not available: {e}. Falling back to memory cache."
                )
                return MemoryCacheBackend()
            except Exception as e:
                logger.warning(
                    f"Redis connection failed: {e}. Falling back to memory cache."
                )
                return MemoryCacheBackend()
        else:
            logger.info("Created memory cache backend")
            return MemoryCacheBackend()

    @staticmethod
    async def create_patient_cache(
        backend: CacheBackend | None = None, default_ttl_minutes: int | None = None
    ) -> PatientDataCache:
        """
        Create patient data cache.

        Args:
            backend: Cache backend to use (creates default if None)
            default_ttl_minutes: Default TTL in minutes (from env or 10)

        Returns:
            PatientDataCache instance
        """
        if backend is None:
            backend = await CacheFactory.create_backend()

        if default_ttl_minutes is None:
            default_ttl_minutes = int(os.getenv("PATIENT_CACHE_TTL_MINUTES", "10"))

        ttl = timedelta(minutes=default_ttl_minutes)

        return PatientDataCache(backend=backend, default_ttl=ttl)
