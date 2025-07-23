"""Integration tests for patient data flow"""

import asyncio

import pytest

from src.services.cache.factory import CacheFactory


class TestPatientDataIntegration:
    """Test patient data caching integration"""

    @pytest.mark.asyncio
    async def test_cache_patient_data(self):
        """Test caching patient data"""
        # Create cache
        cache = await CacheFactory.create_patient_cache()

        # Mock patient data (simplified)
        patient_data = {
            "demographics": {
                "name": "TEST,PATIENT",
                "ssn": "123456789",
                "dob": "19800101",
            },
            "vitals": [{"type": "BP", "value": "120/80", "datetime": "20240115143000"}],
            "labs": [{"test": "Glucose", "value": "95", "unit": "mg/dL"}],
        }

        # Cache it
        station = "500"
        dfn = "12345"
        user_duz = "1089"

        cached = await cache.set_patient_data(station, dfn, user_duz, patient_data)
        assert cached

        # Retrieve it
        retrieved = await cache.get_patient_data(station, dfn, user_duz)
        assert retrieved is not None
        assert retrieved["demographics"]["name"] == "TEST,PATIENT"

        # Check exists
        assert await cache.has_patient_data(station, dfn, user_duz)

        # Invalidate
        assert await cache.invalidate_patient_data(station, dfn, user_duz)
        assert not await cache.has_patient_data(station, dfn, user_duz)

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache TTL expiration"""

        # Create cache with short TTL
        backend = await CacheFactory.create_backend()
        cache = await CacheFactory.create_patient_cache(
            backend=backend, default_ttl_minutes=0.01
        )  # 0.6 seconds

        # Cache data
        await cache.set_patient_data("500", "12345", "1089", {"test": "data"})
        assert await cache.has_patient_data("500", "12345", "1089")

        # Wait for expiration
        await asyncio.sleep(1)

        # Should be expired
        assert not await cache.has_patient_data("500", "12345", "1089")
        assert await cache.get_patient_data("500", "12345", "1089") is None
