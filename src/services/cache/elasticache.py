"""ElastiCache for Redis cache implementation for AWS production use"""

import json
import logging
from datetime import timedelta
from typing import Any

try:
    import boto3
    import redis.asyncio as redis
    from botocore.exceptions import ClientError
    from redis.asyncio import Redis

    HAS_ELASTICACHE = True
except ImportError:
    HAS_ELASTICACHE = False
    Redis = None  # type: ignore[assignment, misc]

from .base import CacheBackend
from .json_encoder import DateTimeJSONEncoder

logger = logging.getLogger(__name__)


class ElastiCacheBackend(CacheBackend):
    """ElastiCache for Redis-based cache backend for AWS production use"""

    def __init__(
        self,
        cluster_endpoint: str,
        port: int = 6379,
        auth_token: str | None = None,
        key_prefix: str = "mcp:",
        region: str = "us-east-1",
        connection_pool_kwargs: dict[str, Any] | None = None,
    ):
        """
        Initialize ElastiCache backend.

        Args:
            cluster_endpoint: ElastiCache cluster endpoint
            port: Redis port (default: 6379)
            auth_token: Authentication token for Redis AUTH
            key_prefix: Prefix for all keys
            region: AWS region
            connection_pool_kwargs: Additional connection pool arguments
        """
        if not HAS_ELASTICACHE:
            raise ImportError(
                "ElastiCache support not installed. Install with: pip install redis[hiredis] boto3"
            )

        self.cluster_endpoint = cluster_endpoint
        self.port = port
        self.auth_token = auth_token
        self.key_prefix = key_prefix
        self.region = region
        self._redis: Redis | None = None
        self._connection_pool_kwargs = connection_pool_kwargs or {}
        self._cluster_info: dict[str, Any] | None = None

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        return timedelta(hours=2)  # Default 2 hours TTL for ElastiCache

    async def _get_cluster_info(self) -> dict[str, Any]:
        """Get ElastiCache cluster information from AWS."""
        if self._cluster_info is None:
            try:
                # Extract cluster name from endpoint
                # Format: clustername.xxxxx.cache.amazonaws.com
                cluster_name = self.cluster_endpoint.split(".")[0]

                client = boto3.client("elasticache", region_name=self.region)
                response = client.describe_cache_clusters(
                    CacheClusterId=cluster_name, ShowCacheNodeInfo=True
                )

                if response["CacheClusters"]:
                    self._cluster_info = response["CacheClusters"][0]
                    logger.info(f"Retrieved ElastiCache cluster info: {cluster_name}")
                else:
                    logger.warning(f"ElastiCache cluster not found: {cluster_name}")
                    self._cluster_info = {}

            except ClientError as e:
                logger.error(f"Failed to get ElastiCache cluster info: {e}")
                self._cluster_info = {}
            except Exception as e:
                logger.error(f"Unexpected error getting cluster info: {e}")
                self._cluster_info = {}

        return self._cluster_info

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection to ElastiCache."""
        if self._redis is None:
            # Build connection URL
            if self.auth_token:
                redis_url = (
                    f"redis://:{self.auth_token}@{self.cluster_endpoint}:{self.port}/0"
                )
            else:
                redis_url = f"redis://{self.cluster_endpoint}:{self.port}/0"

            # Configure connection pool for ElastiCache
            pool_kwargs = {
                "max_connections": 20,
                "retry_on_timeout": True,
                "socket_keepalive": True,
                "socket_keepalive_options": {},
                **self._connection_pool_kwargs,
            }

            self._redis = redis.from_url(
                redis_url,
                decode_responses=False,  # We'll handle encoding/decoding
                **pool_kwargs,
            )

            # Test connection
            try:
                await self._redis.ping()
                logger.info(
                    f"Connected to ElastiCache at {self.cluster_endpoint}:{self.port}"
                )
            except Exception as e:
                logger.error(f"Failed to connect to ElastiCache: {e}")
                raise

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
            logger.error(f"ElastiCache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            # Encode to JSON using custom encoder for date/datetime objects
            try:
                json_value = json.dumps(value, cls=DateTimeJSONEncoder)
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
            logger.error(f"ElastiCache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            result = await redis_client.delete(prefixed_key)
            return result > 0

        except Exception as e:
            logger.error(f"ElastiCache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            redis_client = await self._get_redis()
            prefixed_key = self._make_key(key)

            return await redis_client.exists(prefixed_key) > 0

        except Exception as e:
            logger.error(f"ElastiCache exists error for key {key}: {e}")
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
            logger.error(f"ElastiCache clear error: {e}")
            return False

    async def close(self) -> None:
        """Close ElastiCache connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.debug("Closed ElastiCache connection")

    async def ping(self) -> bool:
        """Check if ElastiCache is available."""
        try:
            redis_client = await self._get_redis()
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"ElastiCache ping failed: {e}")
            return False

    async def get_cluster_health(self) -> dict[str, Any]:
        """Get ElastiCache cluster health information."""
        try:
            cluster_info = await self._get_cluster_info()

            if not cluster_info:
                return {"status": "unknown", "error": "No cluster info available"}

            # Check Redis connection
            redis_healthy = await self.ping()

            # Get cluster status
            cluster_status = cluster_info.get("CacheClusterStatus", "unknown")

            # Get node information
            nodes = cluster_info.get("CacheNodes", [])
            node_statuses = [node.get("CacheNodeStatus", "unknown") for node in nodes]

            return {
                "status": (
                    "healthy"
                    if redis_healthy and cluster_status == "available"
                    else "unhealthy"
                ),
                "cluster_status": cluster_status,
                "redis_healthy": redis_healthy,
                "node_count": len(nodes),
                "node_statuses": node_statuses,
                "endpoint": self.cluster_endpoint,
                "port": self.port,
                "region": self.region,
            }

        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            return {"status": "error", "error": str(e)}
