#!/usr/bin/env python
"""Test the VPR GET PATIENT DATA JSON RPC"""

import asyncio
import json

import httpx


async def test_vpr_rpc():
    """Test VPR GET PATIENT DATA JSON RPC"""

    # Test with the mock server
    url = "http://localhost:9000/api/v1/rpc/invoke"

    # Test with named array format (production format)
    payload = {
        "context": "VPR APPLICATION PROXY",
        "rpc": "VPR GET PATIENT DATA JSON",
        "jsonResult": True,
        "parameters": [{"namedArray": {"patientId": "100841"}}],
    }

    headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": "test-token",
        "Cookie": "JWT=test-jwt",
        "X-Request-ID": "test-request-123",
    }

    print("Testing VPR GET PATIENT DATA JSON RPC...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"\nResponse (truncated): {json.dumps(data, indent=2)[:500]}...")

                # Check if we got VPR data
                if (
                    isinstance(data, dict)
                    and "data" in data
                    and "items" in data["data"]
                ):
                    items = data["data"]["items"]
                    print(f"\nTotal items: {len(items)}")

                    # Group by type
                    types: dict[str, int] = {}
                    for item in items:
                        uid = item.get("uid", "")
                        if ":" in uid:
                            item_type = uid.split(":")[2]
                            types[item_type] = types.get(item_type, 0) + 1

                    print("\nItem types:")
                    for item_type, count in sorted(types.items()):
                        print(f"  {item_type}: {count}")
                else:
                    print("\nUnexpected response format")
            else:
                print(f"\nError Response: {response.text}")

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(test_vpr_rpc())
