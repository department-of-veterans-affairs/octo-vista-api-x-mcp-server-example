"""Base cache interface for patient data"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any


class CacheBackend(ABC):
    """Abstract base class for cache backends"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all cached data.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close any connections or cleanup resources."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Check if cache is available."""
        pass

    @property
    @abstractmethod
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        pass


class PatientDataCache:
    """High-level interface for caching patient data"""

    def __init__(
        self, backend: CacheBackend, default_ttl: timedelta = timedelta(minutes=10)
    ):
        """
        Initialize patient data cache.

        Args:
            backend: Cache backend implementation
            default_ttl: Default time to live for cached data
        """
        self.backend = backend
        self.default_ttl = default_ttl

    def _make_key(self, station: str, dfn: str, user_duz: str) -> str:
        """
        Create cache key for patient data.

        Args:
            station: Station number
            dfn: Patient DFN
            user_duz: User DUZ (for access control)

        Returns:
            Cache key
        """
        return f"patient:v1:{station}:{dfn}:{user_duz}"

    async def get_patient_data(
        self, station: str, dfn: str, user_duz: str
    ) -> dict[str, Any] | None:
        """
        Get patient data from cache.

        Args:
            station: Station number
            dfn: Patient DFN
            user_duz: User DUZ

        Returns:
            Cached patient data or None
        """
        key = self._make_key(station, dfn, user_duz)
        return await self.backend.get(key)

    async def set_patient_data(
        self,
        station: str,
        dfn: str,
        user_duz: str,
        data: dict[str, Any],
        ttl: timedelta | None = None,
    ) -> bool:
        """
        Cache patient data.

        Args:
            station: Station number
            dfn: Patient DFN
            user_duz: User DUZ
            data: Patient data to cache
            ttl: Override default TTL

        Returns:
            True if successful
        """
        key = self._make_key(station, dfn, user_duz)
        return await self.backend.set(key, data, ttl or self.default_ttl)

    async def invalidate_patient_data(
        self, station: str, dfn: str, user_duz: str
    ) -> bool:
        """
        Invalidate cached patient data.

        Args:
            station: Station number
            dfn: Patient DFN
            user_duz: User DUZ

        Returns:
            True if data was cached and removed
        """
        key = self._make_key(station, dfn, user_duz)
        return await self.backend.delete(key)

    async def has_patient_data(self, station: str, dfn: str, user_duz: str) -> bool:
        """
        Check if patient data is cached.

        Args:
            station: Station number
            dfn: Patient DFN
            user_duz: User DUZ

        Returns:
            True if data is cached
        """
        key = self._make_key(station, dfn, user_duz)
        return await self.backend.exists(key)

    async def close(self) -> None:
        """Close cache backend connections."""
        await self.backend.close()
