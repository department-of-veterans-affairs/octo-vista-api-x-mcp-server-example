#!/usr/bin/env python
"""Test that cache keys are deterministic across Python sessions"""

import hashlib
import json
import subprocess
import sys


def generate_cache_key(station, duz, rpc_name, parameters):
    """Generate cache key using deterministic hash"""
    param_hash = hashlib.md5(
        json.dumps(parameters, sort_keys=True).encode()
    ).hexdigest()[:16]
    return f"{station}:{duz}:{rpc_name}:{param_hash}"


def test_in_current_session():
    """Generate keys in current session"""
    params = [{"namedArray": {"patientId": "; 1000220000V123456"}}]

    # Generate same key multiple times
    key1 = generate_cache_key("500", "10000000219", "VPR GET PATIENT DATA JSON", params)
    key2 = generate_cache_key("500", "10000000219", "VPR GET PATIENT DATA JSON", params)

    assert key1 == key2, f"Keys don't match in same session: {key1} != {key2}"

    return key1


def test_in_subprocess():
    """Generate key in subprocess to simulate different Python session"""
    code = """
import hashlib
import json

params = [{"namedArray": {"patientId": "; 1000220000V123456"}}]
param_hash = hashlib.md5(
    json.dumps(params, sort_keys=True).encode()
).hexdigest()[:16]
cache_key = f"500:10000000219:VPR GET PATIENT DATA JSON:{param_hash}"
print(cache_key)
"""

    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    return result.stdout.strip()


if __name__ == "__main__":
    print("Testing deterministic cache key generation...")
    print()

    # Test 1: Same session
    key1 = test_in_current_session()
    print("✓ Keys match in same session")
    print(f"  Key: {key1}")
    print()

    # Test 2: Different session (subprocess)
    key2 = test_in_subprocess()
    print(f"✓ Key from subprocess: {key2}")
    print()

    # Test 3: Compare across sessions
    if key1 == key2:
        print("✅ SUCCESS: Cache keys are deterministic across Python sessions!")
        print(f"   Both sessions generated: {key1}")
    else:
        print("❌ FAILURE: Cache keys differ across sessions!")
        print(f"   Current session: {key1}")
        print(f"   Subprocess:      {key2}")
        sys.exit(1)

    print()
    print("This ensures that:")
    print(
        "- Same RPC calls will hit the cache regardless of which container/process makes them"
    )
    print("- Redis cache will work correctly across multiple ECS tasks")
    print("- No cache misses due to Python's hash randomization")
