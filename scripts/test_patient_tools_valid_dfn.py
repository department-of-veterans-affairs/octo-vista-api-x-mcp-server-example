#!/usr/bin/env python3
"""Test all patient tools using proper MCP client with valid patient DFNs"""

import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


async def test_patient_tools():
    """Test all patient tools with MCP client"""

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
        },
    )

    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        # Initialize session
        await session.initialize()

        print("Testing Patient Tools via MCP Client")
        print("=" * 60)

        # List available tools
        tools = await session.list_tools()
        patient_tools = [
            t for t in tools.tools if t.name.startswith(("search_", "get_patient_"))
        ]
        print(f"Found {len(patient_tools)} patient tools")

        # Use valid test DFNs from the mock data
        test_dfns = ["100022", "100023", "100024"]  # Anderson, Martinez, Thompson

        # 1. Test search_patients
        print("\n1. Testing search_patients...")
        try:
            # Search for ANDERSON (should find patient 100022)
            result = await session.call_tool(
                "search_patients", arguments={"search_term": "ANDERSON", "limit": 5}
            )
            if result.content and isinstance(result.content[0], TextContent):
                data = json.loads(result.content[0].text)
                if data.get("success"):
                    print(f"✅ Found {len(data.get('patients', []))} patients")
                    for patient in data.get("patients", []):
                        print(f"   - {patient['name']} (DFN: {patient['dfn']})")
                else:
                    print(f"❌ Error: {data.get('error')}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # Test each patient DFN
        for test_dfn in test_dfns:
            print(f"\n--- Testing with patient DFN: {test_dfn} ---")

            # 2. Test get_patient_vitals
            print(f"\n2. Testing get_patient_vitals for DFN {test_dfn}...")
            try:
                result = await session.call_tool(
                    "get_patient_vitals",
                    arguments={"patient_dfn": test_dfn, "days_back": 30},
                )
                if result.content and isinstance(result.content[0], TextContent):
                    data = json.loads(result.content[0].text)
                    if data.get("success"):
                        vitals = data.get("vitals", {})
                        print(f"✅ Retrieved {vitals.get('count', 0)} vitals")
                        if vitals.get("latest"):
                            print("   Latest vitals:")
                            for vtype, vdata in list(vitals["latest"].items())[:3]:
                                print(
                                    f"   - {vtype}: {vdata.get('value')} ({vdata.get('date')})"
                                )
                    else:
                        print(f"❌ Error: {data.get('error')}")
            except Exception as e:
                print(f"❌ Failed: {e}")

            # 3. Test get_patient_labs
            print(f"\n3. Testing get_patient_labs for DFN {test_dfn}...")
            try:
                result = await session.call_tool(
                    "get_patient_labs",
                    arguments={"patient_dfn": test_dfn, "days_back": 90},
                )
                if result.content and isinstance(result.content[0], TextContent):
                    data = json.loads(result.content[0].text)
                    if data.get("success"):
                        labs = data.get("labs", {})
                        print(f"✅ Retrieved {labs.get('count', 0)} labs")
                        print(f"   Abnormal: {labs.get('abnormal_count', 0)}")
                    else:
                        print(f"❌ Error: {data.get('error')}")
            except Exception as e:
                print(f"❌ Failed: {e}")

            # 4. Test get_patient_summary
            print(f"\n4. Testing get_patient_summary for DFN {test_dfn}...")
            try:
                result = await session.call_tool(
                    "get_patient_summary", arguments={"patient_dfn": test_dfn}
                )
                if result.content and isinstance(result.content[0], TextContent):
                    data = json.loads(result.content[0].text)
                    if data.get("success"):
                        patient = data.get("patient", {})
                        print(
                            f"✅ Retrieved summary for {patient.get('name', 'Unknown')}"
                        )
                        print(
                            f"   Age: {patient.get('age')}, Gender: {patient.get('gender')}"
                        )
                        print(
                            f"   Service Connected: {patient.get('service_connected_percent', 0)}%"
                        )
                    else:
                        print(f"❌ Error: {data.get('error')}")
            except Exception as e:
                print(f"❌ Failed: {e}")

            # 5. Test get_patient_consults
            print(f"\n5. Testing get_patient_consults for DFN {test_dfn}...")
            try:
                result = await session.call_tool(
                    "get_patient_consults",
                    arguments={"patient_dfn": test_dfn, "active_only": True},
                )
                if result.content and isinstance(result.content[0], TextContent):
                    data = json.loads(result.content[0].text)
                    if data.get("success"):
                        consults = data.get("consults", {})
                        print(f"✅ Found {consults.get('total', 0)} consults")
                        print(f"   Active: {consults.get('active', 0)}")
                        print(f"   Overdue: {consults.get('overdue', 0)}")
                    else:
                        print(f"❌ Error: {data.get('error')}")
            except Exception as e:
                print(f"❌ Failed: {e}")

        # Test with invalid DFN
        print("\n\n--- Testing error handling with invalid DFN ---")
        print("\n6. Testing error handling with invalid DFN...")
        try:
            result = await session.call_tool(
                "get_patient_vitals",
                arguments={"patient_dfn": "invalid", "days_back": 30},
            )
            if result.content and isinstance(result.content[0], TextContent):
                data = json.loads(result.content[0].text)
                if not data.get("success"):
                    print(f"✅ Properly handled invalid DFN: {data.get('error')}")
                else:
                    print("❌ Should have failed with invalid DFN")
        except Exception as e:
            print(f"✅ Properly failed: {e}")

        print("\n" + "=" * 60)
        print("Testing complete!")


if __name__ == "__main__":
    asyncio.run(test_patient_tools())
