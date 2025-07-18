#!/usr/bin/env python3
"""Test a single patient tool in isolation"""

import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


async def test_single_tool(tool_name: str, args: dict[str, Any]):
    """Test a single tool"""

    # Server command - use the running server
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={
            **os.environ,
            "DANGEROUSLY_OMIT_AUTH": "true",
            "VISTA_API_BASE_URL": "http://localhost:8888",
            "DEFAULT_STATION": "500",
            "DEFAULT_DUZ": "10000000219",
            "CACHE_BACKEND": "memory",  # Force memory cache
        },
    )

    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        # Initialize session
        await session.initialize()

        print(f"Testing {tool_name} with args: {args}")
        print("=" * 60)

        try:
            result = await session.call_tool(tool_name, arguments=args)
            if result.content and isinstance(result.content[0], TextContent):
                data = json.loads(result.content[0].text)
                if data.get("success"):
                    print("✅ Success!")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"❌ Error: {data.get('error')}")
            else:
                print("❌ Unexpected response type")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback

            traceback.print_exc()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_single_patient_tool.py <tool_name>")
        print("\nAvailable tools:")
        print("  - search_patients")
        print("  - get_patient_vitals")
        print("  - get_patient_labs")
        print("  - get_patient_summary")
        print("  - get_patient_consults")
        sys.exit(1)

    tool_name = sys.argv[1]

    # Default test arguments for each tool
    test_args: dict[str, dict[str, Any]] = {
        "search_patients": {"search_term": "ANDERSON", "limit": 5},
        "get_patient_vitals": {"patient_dfn": "100022", "days_back": 30},
        "get_patient_labs": {"patient_dfn": "100022", "days_back": 90},
        "get_patient_summary": {"patient_dfn": "100022"},
        "get_patient_consults": {"patient_dfn": "100022", "active_only": True},
    }

    if tool_name not in test_args:
        print(f"Unknown tool: {tool_name}")
        sys.exit(1)

    await test_single_tool(tool_name, test_args[tool_name])


if __name__ == "__main__":
    asyncio.run(main())
