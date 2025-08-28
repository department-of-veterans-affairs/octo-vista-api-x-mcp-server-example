"""Multi-tier cache backend using AWS caching services"""

import asyncio
import logging
from datetime import timedelta
from typing import Any

from .base import CacheBackend

logger = logging.getLogger(__name__)


class MultiTierCacheBackend(CacheBackend):
    """Multi-tier cache backend using AWS caching services"""

    def __init__(
        self,
        backends: list[CacheBackend],
        tier_names: list[str] | None = None,
        write_through: bool = True,
        read_through: bool = True,
    ):
        """
        Initialize multi-tier cache backend.

        Args:
            backends: List of cache backends in order of preference (fastest first)
            tier_names: Names for each tier (for logging)
            write_through: Whether to write to all tiers
            read_through: Whether to populate faster tiers on cache miss
        """
        if not backends:
            raise ValueError("At least one cache backend must be provided")

        self.backends = backends
        self.tier_names = tier_names or [f"tier_{i}" for i in range(len(backends))]
        self.write_through = write_through
        self.read_through = read_through

        if len(self.tier_names) != len(self.backends):
            raise ValueError("Tier names must match number of backends")

        logger.info(
            f"Initialized multi-tier cache with {len(backends)} tiers: {self.tier_names}"
        )

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        # Use the default TTL from the fastest tier
        return getattr(self.backends[0], "default_ttl", timedelta(minutes=10))

    async def get(self, key: str) -> Any | None:
        """Get value from cache, checking tiers in order."""
        # Try each tier from fastest to slowest
        for i, backend in enumerate(self.backends):
            try:
                value = await backend.get(key)
                if value is not None:
                    logger.debug(
                        f"Cache hit on tier {self.tier_names[i]} for key {key}"
                    )

                    # Populate faster tiers on cache miss (read-through)
                    if self.read_through and i > 0:
                        asyncio.create_task(self._populate_faster_tiers(key, value, i))

                    return value

            except Exception as e:
                logger.warning(f"Error reading from tier {self.tier_names[i]}: {e}")
                continue

        logger.debug(f"Cache miss for key {key} on all tiers")
        return None

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache across tiers."""
        if self.write_through:
            # Write to all tiers concurrently
            tasks = []
            for i, backend in enumerate(self.backends):
                task = asyncio.create_task(
                    self._set_with_logging(backend, key, value, ttl, i)
                )
                tasks.append(task)

            # Wait for all writes to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check if at least one tier succeeded
            success_count = sum(1 for r in results if r is True)
            if success_count > 0:
                logger.debug(
                    f"Successfully cached key {key} on {success_count}/{len(self.backends)} tiers"
                )
                return True
            else:
                logger.error(f"Failed to cache key {key} on all tiers")
                return False
        else:
            # Write to fastest tier only
            try:
                result = await self.backends[0].set(key, value, ttl)
                if result:
                    logger.debug(
                        f"Cached key {key} on fastest tier {self.tier_names[0]}"
                    )
                return result
            except Exception as e:
                logger.error(f"Failed to cache key {key} on fastest tier: {e}")
                return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache across all tiers."""
        tasks = []
        for i, backend in enumerate(self.backends):
            task = asyncio.create_task(self._delete_with_logging(backend, key, i))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Return True if at least one tier succeeded
        success_count = sum(1 for r in results if r is True)
        if success_count > 0:
            logger.debug(
                f"Successfully deleted key {key} on {success_count}/{len(self.backends)} tiers"
            )
            return True
        else:
            logger.warning(f"Failed to delete key {key} on any tier")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in any tier."""
        for i, backend in enumerate(self.backends):
            try:
                if await backend.exists(key):
                    logger.debug(f"Key {key} exists on tier {self.tier_names[i]}")
                    return True
            except Exception as e:
                logger.warning(
                    f"Error checking existence on tier {self.tier_names[i]}: {e}"
                )
                continue

        return False

    async def clear(self) -> bool:
        """Clear all cached data across all tiers."""
        tasks = []
        for i, backend in enumerate(self.backends):
            task = asyncio.create_task(self._clear_with_logging(backend, i))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        if success_count > 0:
            logger.info(
                f"Successfully cleared {success_count}/{len(self.backends)} tiers"
            )
            return True
        else:
            logger.error("Failed to clear any tier")
            return False

    async def close(self) -> None:
        """Close all cache backend connections."""
        tasks = []
        for i, backend in enumerate(self.backends):
            task = asyncio.create_task(self._close_with_logging(backend, i))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Closed all cache backend connections")

    async def ping(self) -> bool:
        """Check if any tier is available."""
        for i, backend in enumerate(self.backends):
            try:
                if await backend.ping():
                    logger.debug(f"Tier {self.tier_names[i]} is available")
                    return True
            except Exception as e:
                logger.warning(f"Tier {self.tier_names[i]} ping failed: {e}")
                continue

        logger.error("All cache tiers are unavailable")
        return False

    async def get_tier_health(self) -> dict[str, Any]:
        """Get health information for all tiers."""
        health_info: dict[str, Any] = {
            "overall_status": "unknown",
            "total_tiers": len(self.backends),
            "available_tiers": 0,
            "tiers": {},
        }

        available_count = 0

        for i, backend in enumerate(self.backends):
            tier_name = self.tier_names[i]
            try:
                if hasattr(backend, "get_cluster_health"):
                    tier_health = await backend.get_cluster_health()
                else:
                    # Fallback health check
                    is_healthy = await backend.ping()
                    tier_health = {
                        "status": "healthy" if is_healthy else "unhealthy",
                        "backend_type": backend.__class__.__name__,
                    }

                health_info["tiers"][tier_name] = tier_health

                if tier_health.get("status") == "healthy":
                    available_count += 1

            except Exception as e:
                logger.error(f"Failed to get health for tier {tier_name}: {e}")
                health_info["tiers"][tier_name] = {"status": "error", "error": str(e)}

        health_info["available_tiers"] = available_count

        # Determine overall status
        if available_count == 0:
            health_info["overall_status"] = "unhealthy"
        elif available_count == len(self.backends):
            health_info["overall_status"] = "healthy"
        else:
            health_info["overall_status"] = "degraded"

        return health_info

    async def _populate_faster_tiers(
        self, key: str, value: Any, source_tier_index: int
    ):
        """Populate faster tiers with data from slower tiers."""
        for i in range(source_tier_index):
            try:
                # Get TTL from source tier if possible
                ttl = None
                if hasattr(self.backends[source_tier_index], "default_ttl"):
                    ttl = self.backends[source_tier_index].default_ttl

                await self.backends[i].set(key, value, ttl)
                logger.debug(
                    f"Populated tier {self.tier_names[i]} with data from tier {self.tier_names[source_tier_index]}"
                )
            except Exception as e:
                logger.warning(f"Failed to populate tier {self.tier_names[i]}: {e}")

    async def _set_with_logging(
        self,
        backend: CacheBackend,
        key: str,
        value: Any,
        ttl: timedelta | None,
        tier_index: int,
    ) -> bool:
        """Set value with logging for a specific tier."""
        try:
            result = await backend.set(key, value, ttl)
            if result:
                logger.debug(
                    f"Successfully cached key {key} on tier {self.tier_names[tier_index]}"
                )
            else:
                logger.warning(
                    f"Failed to cache key {key} on tier {self.tier_names[tier_index]}"
                )
            return result
        except Exception as e:
            logger.error(
                f"Error caching key {key} on tier {self.tier_names[tier_index]}: {e}"
            )
            return False

    async def _delete_with_logging(
        self, backend: CacheBackend, key: str, tier_index: int
    ) -> bool:
        """Delete value with logging for a specific tier."""
        try:
            result = await backend.delete(key)
            if result:
                logger.debug(
                    f"Successfully deleted key {key} on tier {self.tier_names[tier_index]}"
                )
            return result
        except Exception as e:
            logger.error(
                f"Error deleting key {key} on tier {self.tier_names[tier_index]}: {e}"
            )
            return False

    async def _clear_with_logging(self, backend: CacheBackend, tier_index: int) -> bool:
        """Clear cache with logging for a specific tier."""
        try:
            result = await backend.clear()
            if result:
                logger.info(f"Successfully cleared tier {self.tier_names[tier_index]}")
            return result
        except Exception as e:
            logger.error(f"Error clearing tier {self.tier_names[tier_index]}: {e}")
            return False

    async def _close_with_logging(self, backend: CacheBackend, tier_index: int) -> None:
        """Close backend with logging for a specific tier."""
        try:
            await backend.close()
            logger.debug(f"Successfully closed tier {self.tier_names[tier_index]}")
        except Exception as e:
            logger.error(f"Error closing tier {self.tier_names[tier_index]}: {e}")

    def get_tier_info(self) -> dict[str, Any]:
        """Get information about all tiers."""
        return {
            "tier_count": len(self.backends),
            "tiers": [
                {
                    "name": self.tier_names[i],
                    "type": backend.__class__.__name__,
                    "index": i,
                }
                for i, backend in enumerate(self.backends)
            ],
            "write_through": self.write_through,
            "read_through": self.read_through,
        }
