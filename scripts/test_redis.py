#!/usr/bin/env python
# mypy: ignore-errors
"""Test Redis configuration and functionality"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cache.factory import CacheFactory
from cache.redis import RedisCacheBackend


async def test_redis_connection():
    """Test basic Redis connectivity"""
    print("🔧 Testing Redis Connection...")

    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"   Redis URL: {redis_url}")

    try:
        # Create Redis backend directly
        redis_cache = RedisCacheBackend(redis_url=redis_url, key_prefix="test:")

        # Test ping
        if await redis_cache.ping():
            print("✅ Redis connection successful!")
        else:
            print("❌ Redis ping failed")
            return False

        # Cleanup
        await redis_cache.close()
        return True

    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False


async def test_basic_operations():
    """Test basic cache operations"""
    print("\n📝 Testing Basic Cache Operations...")

    cache = await CacheFactory.create_backend()

    try:
        # Test set/get with string
        print("   Testing string value...")
        await cache.set("test:string", "Hello Redis!", ttl=timedelta(seconds=60))
        value = await cache.get("test:string")
        assert value == "Hello Redis!", f"Expected 'Hello Redis!', got {value}"
        print("   ✅ String storage works")

        # Test set/get with dict
        print("   Testing dictionary value...")
        test_dict = {
            "name": "Test Patient",
            "id": "12345",
            "timestamp": datetime.now().isoformat(),
        }
        await cache.set("test:dict", test_dict, ttl=timedelta(seconds=60))
        retrieved = await cache.get("test:dict")
        assert retrieved["name"] == test_dict["name"], "Dictionary retrieval failed"
        print("   ✅ Dictionary storage works")

        # Test exists
        print("   Testing key existence...")
        exists = await cache.exists("test:string")
        assert exists, "Key should exist"
        not_exists = await cache.exists("test:nonexistent")
        assert not not_exists, "Non-existent key check failed"
        print("   ✅ Existence check works")

        # Test delete
        print("   Testing deletion...")
        deleted = await cache.delete("test:string")
        assert deleted, "Delete should return True"
        exists_after = await cache.exists("test:string")
        assert not exists_after, "Key should not exist after deletion"
        print("   ✅ Deletion works")

        # Cleanup
        await cache.delete("test:dict")
        await cache.close()

        print("\n✅ All basic operations passed!")
        return True

    except Exception as e:
        print(f"\n❌ Basic operations test failed: {e}")
        await cache.close()
        return False


async def test_patient_data_caching():
    """Test caching patient data models"""
    print("\n🏥 Testing Patient Data Caching...")

    cache = await CacheFactory.create_backend()

    try:
        # Create sample patient data
        patient_data = {
            "demographics": {
                "dfn": "100841",
                "icn": "1005555555V666666",
                "ssn": "666-12-3456",
                "fullName": "TEST,PATIENT ONE",
                "familyName": "TEST",
                "givenNames": "PATIENT ONE",
                "dateOfBirth": 19450815,
                "genderCode": "M",
                "genderName": "MALE",
                "addresses": [
                    {
                        "streetLine1": "123 TEST ST",
                        "city": "TESTVILLE",
                        "stateProvince": "FL",
                        "postalCode": "12345",
                    }
                ],
                "telecoms": [
                    {
                        "telecom": "555-1234",
                        "usageCode": "HP",
                        "usageName": "home phone",
                    }
                ],
            },
            "vital_signs": [],
            "lab_results": [],
            "consults": [],
            "source_station": "500",
            "source_dfn": "100841",
            "total_items": 1,
        }

        # Create cache key
        cache_key = "patient:v1:500:100841:10000000219"

        # Store patient data
        print(f"   Storing patient data with key: {cache_key}")
        stored = await cache.set(cache_key, patient_data, ttl=timedelta(minutes=10))
        assert stored, "Failed to store patient data"
        print("   ✅ Patient data stored")

        # Retrieve patient data
        print("   Retrieving patient data...")
        retrieved = await cache.get(cache_key)
        assert retrieved is not None, "Failed to retrieve patient data"
        assert retrieved["demographics"]["dfn"] == "100841", "DFN mismatch"
        assert (
            retrieved["demographics"]["fullName"] == "TEST,PATIENT ONE"
        ), "Name mismatch"
        print("   ✅ Patient data retrieved correctly")

        # Test TTL info (Redis-specific)
        if isinstance(cache, RedisCacheBackend):
            redis_client = await cache._get_redis()
            ttl_seconds = await redis_client.ttl(cache._make_key(cache_key))
            print(
                f"   ℹ️  TTL remaining: {ttl_seconds} seconds (~{ttl_seconds//60} minutes)"
            )

        # Cleanup
        await cache.delete(cache_key)
        await cache.close()

        print("\n✅ Patient data caching test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Patient data caching test failed: {e}")
        await cache.close()
        return False


async def test_cache_factory():
    """Test cache factory with different backends"""
    print("\n🏭 Testing Cache Factory...")

    # Test with explicit Redis backend
    print("   Testing Redis backend selection...")
    os.environ["CACHE_BACKEND"] = "redis"
    cache = await CacheFactory.create_backend()
    assert isinstance(cache, RedisCacheBackend), "Should create Redis backend"
    await cache.close()
    print("   ✅ Redis backend created")

    # Test with memory backend
    print("   Testing memory backend selection...")
    os.environ["CACHE_BACKEND"] = "memory"
    cache = await CacheFactory.create_backend()
    assert (
        cache.__class__.__name__ == "MemoryCacheBackend"
    ), "Should create Memory backend"
    await cache.close()
    print("   ✅ Memory backend created")

    # Reset to Redis for other tests
    os.environ["CACHE_BACKEND"] = "redis"

    print("\n✅ Cache factory test passed!")
    return True


async def main():
    """Run all Redis tests"""
    print("🚀 Redis Configuration Test Suite")
    print("=" * 50)

    # Check if Redis is running
    redis_running = await test_redis_connection()
    if not redis_running:
        print("\n⚠️  Redis is not running!")
        print("\nTo start Redis:")
        print("  Option 1: docker-compose up -d redis")
        print("  Option 2: redis-server (if installed locally)")
        print("  Option 3: brew services start redis (on macOS)")
        return

    # Run tests
    all_passed = True
    all_passed &= await test_basic_operations()
    all_passed &= await test_patient_data_caching()
    all_passed &= await test_cache_factory()

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All Redis tests passed!")
        print("\nRedis is properly configured and working.")
        print("\nTo use Redis in the MCP server:")
        print("  1. Ensure Redis is running: docker-compose up -d redis")
        print("  2. Set environment variable: export CACHE_BACKEND=redis")
        print("  3. Optionally set: export REDIS_URL=redis://localhost:6379/0")
    else:
        print("❌ Some tests failed. Check the output above.")


if __name__ == "__main__":
    asyncio.run(main())
