"""Local development cache backend for simulating AWS caching services"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from .base import CacheBackend

logger = logging.getLogger(__name__)


class LocalDevCacheBackend(CacheBackend):
    """Local development cache backend that simulates AWS caching services"""

    def __init__(
        self,
        backend_type: str = "elasticache",
        key_prefix: str = "mcp:",
        max_size: int = 1000,
        enable_persistence: bool = False,
        persistence_file: str = "local_cache.json",
    ):
        """
        Initialize local development cache backend.

        Args:
            backend_type: Type of AWS service to simulate ("elasticache", "memcached", "dax")
            key_prefix: Prefix for all keys
            max_size: Maximum number of cached items
            enable_persistence: Whether to persist cache to disk
            persistence_file: File path for persistence
        """
        self.backend_type = backend_type
        self.key_prefix = key_prefix
        self.max_size = max_size
        self.enable_persistence = enable_persistence
        self.persistence_file = persistence_file

        # In-memory storage
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        # Load persistent data if enabled
        if self.enable_persistence:
            self._load_persistence()

        logger.info(f"Initialized local dev cache backend simulating {backend_type}")

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    def _is_expired(self, item: dict[str, Any]) -> bool:
        """Check if cache item is expired."""
        if "expires_at" not in item:
            return False

        now = datetime.now(UTC)
        expires_at = datetime.fromisoformat(item["expires_at"])
        return now > expires_at

    def _cleanup_expired(self) -> None:
        """Remove expired items from cache."""
        now = datetime.now(UTC)
        expired_keys = []

        for key, item in self._cache.items():
            if "expires_at" in item:
                expires_at = datetime.fromisoformat(item["expires_at"])
                if now > expires_at:
                    expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")

    def _enforce_max_size(self) -> None:
        """Enforce maximum cache size by removing oldest items."""
        if len(self._cache) <= self.max_size:
            return

        # Sort by creation time and remove oldest
        sorted_items = sorted(
            self._cache.items(), key=lambda x: x[1].get("created_at", "0")
        )

        items_to_remove = len(self._cache) - self.max_size
        for i in range(items_to_remove):
            key, _ = sorted_items[i]
            del self._cache[key]

        logger.debug(f"Enforced max size by removing {items_to_remove} oldest items")

    def _save_persistence(self) -> None:
        """Save cache data to disk."""
        if not self.enable_persistence:
            return

        try:
            with open(self.persistence_file, "w") as f:
                json.dump(self._cache, f, indent=2)
            logger.debug(f"Saved cache persistence to {self.persistence_file}")
        except Exception as e:
            logger.error(f"Failed to save cache persistence: {e}")

    def _load_persistence(self) -> None:
        """Load cache data from disk."""
        if not self.enable_persistence:
            return

        try:
            with open(self.persistence_file) as f:
                self._cache = json.load(f)
            logger.debug(f"Loaded cache persistence from {self.persistence_file}")
        except FileNotFoundError:
            logger.debug("No persistence file found, starting with empty cache")
        except Exception as e:
            logger.error(f"Failed to load cache persistence: {e}")

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            prefixed_key = self._make_key(key)

            if prefixed_key not in self._cache:
                return None

            item = self._cache[prefixed_key]

            # Check if expired
            if self._is_expired(item):
                del self._cache[prefixed_key]
                logger.debug(f"Cache key {key} expired and removed")
                return None

            # Update access time
            item["last_accessed"] = datetime.now(UTC).isoformat()

            logger.debug(f"Cache hit for key {key}")
            return item["value"]

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache."""
        async with self._lock:
            prefixed_key = self._make_key(key)
            now = datetime.now(UTC)

            # Create cache item
            item = {
                "value": value,
                "created_at": now.isoformat(),
                "last_accessed": now.isoformat(),
            }

            if ttl:
                expires_at = now + ttl
                item["expires_at"] = expires_at.isoformat()

            # Store in cache
            self._cache[prefixed_key] = item

            # Cleanup and enforce limits
            self._cleanup_expired()
            self._enforce_max_size()

            # Save persistence if enabled
            if self.enable_persistence:
                self._save_persistence()

            logger.debug(f"Cached key {key} with TTL {ttl}")
            return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            prefixed_key = self._make_key(key)

            if prefixed_key in self._cache:
                del self._cache[prefixed_key]

                # Save persistence if enabled
                if self.enable_persistence:
                    self._save_persistence()

                logger.debug(f"Deleted cache key {key}")
                return True

            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        async with self._lock:
            prefixed_key = self._make_key(key)

            if prefixed_key not in self._cache:
                return False

            # Check if expired
            if self._is_expired(self._cache[prefixed_key]):
                del self._cache[prefixed_key]
                return False

            return True

    async def clear(self) -> bool:
        """Clear all cached data."""
        async with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()

            # Save persistence if enabled
            if self.enable_persistence:
                self._save_persistence()

            logger.info(f"Cleared {cleared_count} cache items")
            return True

    async def close(self) -> None:
        """Close cache backend and save persistence."""
        async with self._lock:
            if self.enable_persistence:
                self._save_persistence()
            logger.debug("Closed local dev cache backend")

    async def ping(self) -> bool:
        """Check if cache is available."""
        return True

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        return timedelta(minutes=10)  # Default 10 minutes TTL for local dev cache

    async def get_cluster_health(self) -> dict[str, Any]:
        """Get simulated cluster health information."""

        # Calculate cache statistics
        total_items = len(self._cache)
        expired_items = 0
        active_items = 0

        for item in self._cache.values():
            if self._is_expired(item):
                expired_items += 1
            else:
                active_items += 1

        return {
            "status": "healthy",
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
            "simulation_info": {
                "backend_type": self.backend_type,
                "persistence_enabled": self.enable_persistence,
                "persistence_file": (
                    self.persistence_file if self.enable_persistence else None
                ),
            },
        }

    def get_stats(self) -> dict[str, Any]:
        """Get detailed cache statistics."""

        # Calculate various statistics
        total_items = len(self._cache)
        expired_items = 0
        active_items = 0
        total_size_bytes = 0

        for item in self._cache.values():
            if self._is_expired(item):
                expired_items += 1
            else:
                active_items += 1
                # Estimate size (rough calculation)
                try:
                    item_size = len(json.dumps(item["value"]))
                    total_size_bytes += item_size
                except (TypeError, ValueError):
                    total_size_bytes += 100  # Default estimate

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
        }

    def simulate_failure(self, failure_type: str = "connection") -> None:
        """Simulate various failure scenarios for testing."""
        if failure_type == "connection":
            # Simulate connection failure
            self._cache.clear()
            logger.warning("Simulated connection failure - cache cleared")
        elif failure_type == "memory_pressure":
            # Simulate memory pressure by reducing max size
            original_max = self.max_size
            self.max_size = max(1, self.max_size // 10)
            self._enforce_max_size()
            logger.warning(
                f"Simulated memory pressure - max size reduced from {original_max} to {self.max_size}"
            )
        elif failure_type == "corruption":
            # Simulate data corruption
            if self._cache:
                # Corrupt a random item
                import random

                keys = list(self._cache.keys())
                if keys:
                    corrupt_key = random.choice(keys)
                    self._cache[corrupt_key]["value"] = "CORRUPTED_DATA"
                    logger.warning(f"Simulated data corruption for key {corrupt_key}")
        else:
            logger.warning(f"Unknown failure type: {failure_type}")

    def reset_simulation(self) -> None:
        """Reset any simulated failure conditions."""
        # Restore original max size if it was modified
        if hasattr(self, "_original_max_size"):
            self.max_size = self._original_max_size
            delattr(self, "_original_max_size")

        logger.info("Reset simulation conditions")
