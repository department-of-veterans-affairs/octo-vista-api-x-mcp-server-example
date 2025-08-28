"""Factory for creating cache backends"""

import logging
import os
from datetime import timedelta
from typing import Any

from .base import CacheBackend, PatientDataCache
from .dax import DAXBackend
from .elasticache import ElastiCacheBackend
from .local_dev import LocalDevCacheBackend
from .local_dev_redis import LocalDevRedisBackend
from .memory import MemoryCacheBackend
from .multi_tier import MultiTierCacheBackend
from .redis import RedisCacheBackend

logger = logging.getLogger(__name__)


class CacheFactory:
    """Factory for creating cache backends"""

    @staticmethod
    async def create_backend() -> CacheBackend:
        """
        Create cache backend based on environment configuration.

        Environment variables:
            CACHE_BACKEND: "elasticache", "dax", "redis", "multi-tier", "local-dev", "local-dev-redis", or "memory"
            AWS_CACHE_BACKEND: "elasticache" or "dax" (for AWS-specific configs)

            # ElastiCache for Redis
            ELASTICACHE_ENDPOINT: ElastiCache cluster endpoint
            ELASTICACHE_PORT: Redis port (default: 6379)
            ELASTICACHE_AUTH_TOKEN: Authentication token

            # DynamoDB Accelerator (DAX)
            DAX_ENDPOINT: DAX cluster endpoint
            DAX_TABLE_NAME: DynamoDB table name (default: "vista_cache")

            # Redis (fallback)
            REDIS_URL: Redis connection URL

            # Local Development
            LOCAL_CACHE_BACKEND_TYPE: Type to simulate ("elasticache", "dax")
            LOCAL_CACHE_MAX_SIZE: Maximum cache size (default: 1000)
            LOCAL_CACHE_PERSISTENCE: Enable persistence (default: false)
            LOCAL_CACHE_PERSISTENCE_FILE: Persistence file path

            # Enhanced Local Development with Redis
            LOCAL_REDIS_URL: Local Redis URL (default: redis://localhost:6379)
            LOCAL_REDIS_PASSWORD: Local Redis password (default: local_dev_password)
            LOCAL_REDIS_FALLBACK: Enable memory fallback (default: true)

            # General
            CACHE_KEY_PREFIX: Prefix for all cache keys (default: "mcp:")
            AWS_REGION: AWS region (default: "us-east-1")

        Returns:
            Cache backend instance
        """
        backend_type = os.getenv("CACHE_BACKEND", "memory").lower()

        # Local Development (Priority 1 - for development/testing)
        if backend_type == "local-dev-redis":
            return await CacheFactory._create_local_dev_redis_backend()
        elif backend_type == "local-dev":
            return CacheFactory._create_local_dev_backend()

        # AWS Caching Services (Priority 2 - production)
        elif backend_type in ["elasticache", "aws"]:
            return await CacheFactory._create_elasticache_backend()

        elif backend_type == "dax":
            return await CacheFactory._create_dax_backend()

        elif backend_type == "multi-tier":
            return await CacheFactory._create_multi_tier_backend()

        # Redis (Priority 3 - fallback)
        elif backend_type == "redis":
            return await CacheFactory._create_redis_backend()

        # Memory (Priority 4 - last resort, deprecated)
        elif backend_type == "memory":
            logger.warning(
                "Memory cache is deprecated and should not be used in production"
            )
            return MemoryCacheBackend()

        else:
            # Default to ElastiCache, fallback to Redis, then memory
            logger.info(
                f"Unknown cache backend '{backend_type}', trying ElastiCache first"
            )
            try:
                return await CacheFactory._create_elasticache_backend()
            except Exception as e:
                logger.warning(f"ElastiCache failed: {e}, trying Redis")
                try:
                    return await CacheFactory._create_redis_backend()
                except Exception as e2:
                    logger.warning(
                        f"Redis failed: {e2}, falling back to memory (DEPRECATED)"
                    )
                    return MemoryCacheBackend()

    @staticmethod
    async def _create_local_dev_redis_backend() -> LocalDevRedisBackend:
        """Create enhanced local development cache backend with Redis fallback."""
        backend_type = os.getenv("LOCAL_CACHE_BACKEND_TYPE", "elasticache")
        key_prefix = os.getenv("CACHE_KEY_PREFIX", "mcp:")
        max_size = int(os.getenv("LOCAL_CACHE_MAX_SIZE", "1000"))
        enable_persistence = (
            os.getenv("LOCAL_CACHE_PERSISTENCE", "false").lower() == "true"
        )
        persistence_file = os.getenv("LOCAL_CACHE_PERSISTENCE_FILE", "local_cache.json")

        # Redis configuration
        redis_url = os.getenv("LOCAL_REDIS_URL", "redis://localhost:6379")
        redis_password = os.getenv("LOCAL_REDIS_PASSWORD", "local_dev_password")
        fallback_to_memory = os.getenv("LOCAL_REDIS_FALLBACK", "true").lower() == "true"

        logger.info(
            f"Creating enhanced local dev cache with Redis fallback (type: {backend_type})"
        )
        return LocalDevRedisBackend(
            backend_type=backend_type,
            key_prefix=key_prefix,
            max_size=max_size,
            enable_persistence=enable_persistence,
            persistence_file=persistence_file,
            redis_url=redis_url,
            redis_password=redis_password,
            fallback_to_memory=fallback_to_memory,
        )

    @staticmethod
    def _create_local_dev_backend() -> LocalDevCacheBackend:
        """Create local development cache backend."""
        backend_type = os.getenv("LOCAL_CACHE_BACKEND_TYPE", "elasticache")
        key_prefix = os.getenv("CACHE_KEY_PREFIX", "mcp:")
        max_size = int(os.getenv("LOCAL_CACHE_MAX_SIZE", "1000"))
        enable_persistence = (
            os.getenv("LOCAL_CACHE_PERSISTENCE", "false").lower() == "true"
        )
        persistence_file = os.getenv("LOCAL_CACHE_PERSISTENCE_FILE", "local_cache.json")

        logger.info(f"Created local dev cache backend simulating {backend_type}")
        return LocalDevCacheBackend(
            backend_type=backend_type,
            key_prefix=key_prefix,
            max_size=max_size,
            enable_persistence=enable_persistence,
            persistence_file=persistence_file,
        )

    @staticmethod
    async def _create_elasticache_backend() -> ElastiCacheBackend:
        """Create ElastiCache for Redis backend."""
        endpoint = os.getenv("ELASTICACHE_ENDPOINT")
        if not endpoint:
            raise ValueError(
                "ELASTICACHE_ENDPOINT environment variable is required for ElastiCache"
            )

        port = int(os.getenv("ELASTICACHE_PORT", "6379"))
        auth_token = os.getenv("ELASTICACHE_AUTH_TOKEN")
        region = os.getenv("AWS_REGION", "us-east-1")
        key_prefix = os.getenv("CACHE_KEY_PREFIX", "mcp:")

        try:
            backend = ElastiCacheBackend(
                cluster_endpoint=endpoint,
                port=port,
                auth_token=auth_token,
                key_prefix=key_prefix,
                region=region,
            )

            # Test connection
            if await backend.ping():
                logger.info(f"Created ElastiCache backend with endpoint: {endpoint}")
                return backend
            else:
                raise ConnectionError("ElastiCache ping failed")

        except Exception as e:
            logger.error(f"Failed to create ElastiCache backend: {e}")
            raise

    @staticmethod
    async def _create_dax_backend() -> DAXBackend:
        """Create DynamoDB Accelerator (DAX) backend."""
        endpoint = os.getenv("DAX_ENDPOINT")
        if not endpoint:
            raise ValueError("DAX_ENDPOINT environment variable is required for DAX")

        region = os.getenv("AWS_REGION", "us-east-1")
        key_prefix = os.getenv("CACHE_KEY_PREFIX", "mcp:")
        table_name = os.getenv("DAX_TABLE_NAME", "vista_cache")

        try:
            backend = DAXBackend(
                cluster_endpoint=endpoint,
                region=region,
                key_prefix=key_prefix,
                table_name=table_name,
            )

            # Test connection
            if await backend.ping():
                logger.info(f"Created DAX backend with endpoint: {endpoint}")
                return backend
            else:
                raise ConnectionError("DAX ping failed")

        except Exception as e:
            logger.error(f"Failed to create DAX backend: {e}")
            raise

    @staticmethod
    async def _create_redis_backend() -> RedisCacheBackend:
        """Create Redis backend (fallback)."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        key_prefix = os.getenv("CACHE_KEY_PREFIX", "mcp:")

        try:
            backend = RedisCacheBackend(redis_url=redis_url, key_prefix=key_prefix)
            # Test connection
            if await backend.ping():
                logger.info(f"Created Redis cache backend with URL: {redis_url}")
                return backend
            else:
                raise ConnectionError("Redis ping failed")
        except Exception as e:
            logger.error(f"Failed to create Redis backend: {e}")
            raise

    @staticmethod
    async def _create_multi_tier_backend() -> MultiTierCacheBackend:
        """Create multi-tier cache backend."""
        backends: list[CacheBackend] = []
        tier_names: list[str] = []

        # Try to create AWS backends first
        try:
            elasticache = await CacheFactory._create_elasticache_backend()
            backends.append(elasticache)
            tier_names.append("elasticache")
        except Exception as e:
            logger.warning(f"ElastiCache not available for multi-tier: {e}")

        try:
            dax = await CacheFactory._create_dax_backend()
            backends.append(dax)
            tier_names.append("dax")
        except Exception as e:
            logger.warning(f"DAX not available for multi-tier: {e}")

        # Add Redis as fallback
        try:
            redis = await CacheFactory._create_redis_backend()
            backends.append(redis)
            tier_names.append("redis")
        except Exception as e:
            logger.warning(f"Redis not available for multi-tier: {e}")

        if not backends:
            raise ValueError("No cache backends available for multi-tier configuration")

        # Configure multi-tier behavior
        write_through = os.getenv("MULTI_TIER_WRITE_THROUGH", "true").lower() == "true"
        read_through = os.getenv("MULTI_TIER_READ_THROUGH", "true").lower() == "true"

        logger.info(
            f"Created multi-tier cache with {len(backends)} backends: {tier_names}"
        )
        return MultiTierCacheBackend(
            backends=backends,
            tier_names=tier_names,
            write_through=write_through,
            read_through=read_through,
        )

    @staticmethod
    async def create_patient_cache(
        backend: CacheBackend | None = None, default_ttl_minutes: int | None = None
    ) -> PatientDataCache:
        """
        Create patient data cache with updated TTL configuration.

        Args:
            backend: Cache backend to use (creates default if None)
            default_ttl_minutes: Default TTL in minutes (from env or 20)

        Returns:
            PatientDataCache instance
        """
        if backend is None:
            backend = await CacheFactory.create_backend()

        if default_ttl_minutes is None:
            # Updated TTL: increased from 10 to 20 minutes
            default_ttl_minutes = int(os.getenv("PATIENT_CACHE_TTL_MINUTES", "20"))

        ttl = timedelta(minutes=default_ttl_minutes)

        return PatientDataCache(backend=backend, default_ttl=ttl)

    @staticmethod
    def get_cache_config() -> dict[str, Any]:
        """Get current cache configuration."""
        return {
            "backend_type": os.getenv("CACHE_BACKEND", "elasticache"),
            "aws_backend": os.getenv("AWS_CACHE_BACKEND", "elasticache"),
            "patient_cache_ttl_minutes": int(
                os.getenv("PATIENT_CACHE_TTL_MINUTES", "20")
            ),
            "token_cache_ttl_minutes": int(os.getenv("TOKEN_CACHE_TTL_MINUTES", "55")),
            "response_cache_ttl_minutes": int(
                os.getenv("RESPONSE_CACHE_TTL_MINUTES", "10")
            ),
            "elasticache_endpoint": os.getenv("ELASTICACHE_ENDPOINT"),
            "dax_endpoint": os.getenv("DAX_ENDPOINT"),
            "redis_url": os.getenv("REDIS_URL"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "key_prefix": os.getenv("CACHE_KEY_PREFIX", "mcp:"),
            "local_dev": {
                "backend_type": os.getenv("LOCAL_CACHE_BACKEND_TYPE", "elasticache"),
                "max_size": int(os.getenv("LOCAL_CACHE_MAX_SIZE", "1000")),
                "persistence_enabled": os.getenv(
                    "LOCAL_CACHE_PERSISTENCE", "false"
                ).lower()
                == "true",
                "persistence_file": os.getenv(
                    "LOCAL_CACHE_PERSISTENCE_FILE", "local_cache.json"
                ),
            },
            "local_dev_redis": {
                "redis_url": os.getenv("LOCAL_REDIS_URL", "redis://localhost:6379"),
                "redis_password": os.getenv(
                    "LOCAL_REDIS_PASSWORD", "local_dev_password"
                ),
                "fallback_to_memory": os.getenv("LOCAL_REDIS_FALLBACK", "true").lower()
                == "true",
            },
        }
