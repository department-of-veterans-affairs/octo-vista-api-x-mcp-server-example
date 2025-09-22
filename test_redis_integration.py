#!/usr/bin/env python
"""Test script to verify Redis integration with VistaAPIClient"""

import asyncio
import os
import time

import redis
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Ensure Redis is configured
os.environ["CACHE_BACKEND"] = "redis"
os.environ["REDIS_URL"] = "redis://:local_dev_password@localhost:6379/0"
os.environ["CACHE_KEY_PREFIX"] = "vista_mcp:"


async def test_redis_caching():
    """Test that VistaAPIClient uses Redis for caching"""

    print("\n=== Testing Redis Integration with VistaAPIClient ===\n")

    # Import after setting environment
    from src.vista.client import VistaAPIClient

    # Create client
    print("1. Creating VistaAPIClient...")
    client = VistaAPIClient(
        base_url=os.getenv("VISTA_API_BASE_URL", "http://localhost:8888"),
        auth_url=os.getenv("VISTA_AUTH_URL", "http://localhost:8888"),
        api_key=os.getenv("VISTA_API_KEY", "test-wildcard-key-456"),
    )

    print(
        f"   Initial cache backend: {type(client.response_cache_backend).__name__ if client.response_cache_backend else 'TTLCache'}"
    )

    # Make a test RPC call (this will trigger lazy initialization)
    print("\n2. Making test RPC call...")
    try:
        _ = await client.invoke_rpc(
            station="500",
            caller_duz="10000000219",
            rpc_name="VPR GET PATIENT DATA JSON",
            parameters=[{"namedArray": {"patientId": "; 1000220000V123456"}}],
            json_result=True,
        )
        print("   ✓ RPC call successful")
    except Exception as e:
        print(f"   RPC call failed (expected if mock server not running): {e}")

    # Check if Redis is being used after initialization
    print(
        f"\n3. Cache backend after initialization: {type(client.response_cache_backend).__name__ if client.response_cache_backend else 'TTLCache'}"
    )

    # Check Redis directly
    print("\n4. Checking Redis directly...")
    try:
        r = redis.Redis(
            host="localhost",
            port=6379,
            password="local_dev_password",
            decode_responses=True,
        )
        r.ping()

        # Look for cache keys
        all_keys = r.keys("*")
        rpc_keys = [k for k in all_keys if "VPR" in k or "rpc" in k.lower()]

        print(f"   Total Redis keys: {len(all_keys)}")
        print(f"   RPC-related keys: {len(rpc_keys)}")

        if rpc_keys:
            print("\n   Sample RPC cache keys:")
            for key in rpc_keys[:3]:
                ttl = r.ttl(key)
                print(f"     - {key} (TTL: {ttl}s)")

            print("\n   ✅ Redis caching is working!")
        else:
            print("\n   ⚠️  No RPC cache keys found in Redis")

    except redis.ConnectionError:
        print("   ✗ Redis not accessible")

    # Clean up
    await client.close()
    print("\n✓ Test complete")


async def test_cache_performance():
    """Test cache performance improvement"""

    print("\n=== Testing Cache Performance ===\n")

    from src.vista.client import VistaAPIClient

    client = VistaAPIClient(
        base_url=os.getenv("VISTA_API_BASE_URL", "http://localhost:8888"),
        auth_url=os.getenv("VISTA_AUTH_URL", "http://localhost:8888"),
        api_key=os.getenv("VISTA_API_KEY", "test-wildcard-key-456"),
    )

    params = [{"namedArray": {"patientId": "; 1000220000V123456"}}]

    try:
        # First call (should hit API)
        print("1. First RPC call (uncached)...")
        start = time.time()
        _ = await client.invoke_rpc(
            station="500",
            caller_duz="10000000219",
            rpc_name="VPR GET PATIENT DATA JSON",
            parameters=params,
            json_result=True,
        )
        time1 = time.time() - start
        print(f"   Time: {time1:.3f}s")

        # Second call (should use cache)
        print("\n2. Second RPC call (cached)...")
        start = time.time()
        _ = await client.invoke_rpc(
            station="500",
            caller_duz="10000000219",
            rpc_name="VPR GET PATIENT DATA JSON",
            parameters=params,
            json_result=True,
        )
        time2 = time.time() - start
        print(f"   Time: {time2:.3f}s")

        if time2 < time1 / 5:
            print(f"\n   ✅ Cache is working! {time1/time2:.1f}x speedup")
        else:
            print(
                f"\n   ⚠️  Cache may not be working optimally (only {time1/time2:.1f}x speedup)"
            )

    except Exception as e:
        print(f"   Error: {e}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(test_redis_caching())
    asyncio.run(test_cache_performance())
