#!/usr/bin/env python3
"""Check if mock server is running - cross-platform"""

import sys
import time

import httpx


def check_mock_server(url="http://localhost:8080/health", max_attempts=10):
    """Check if mock server is running"""
    print(f"Checking mock server at {url}...")

    for attempt in range(max_attempts):
        try:
            response = httpx.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ Mock server is running")
                return True
        except:
            if attempt < max_attempts - 1:
                print(
                    f"⏳ Waiting for mock server... (attempt {attempt + 1}/{max_attempts})"
                )
                time.sleep(2)
            else:
                print("❌ Mock server is not responding")
                return False

    return False


if __name__ == "__main__":
    sys.exit(0 if check_mock_server() else 1)
