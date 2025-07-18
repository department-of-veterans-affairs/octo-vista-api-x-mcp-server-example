#!/usr/bin/env python
"""Test MCP client for patient tools"""

import asyncio
import json
import os

# Add src to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


async def test_patient_tools():
    """Test patient tools with MCP client"""

    # Server command
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp", "dev", "server.py:server"],
        env={
            **os.environ,
            "DANGEROUSLY_OMIT_AUTH": "true",
            "VISTA_API_BASE_URL": "http://localhost:9000",
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

        # List available tools
        tools = await session.list_tools()
        print("Available tools:")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\n" + "=" * 60 + "\n")

        # Test 1: Search patients
        print("Test 1: Searching for patients...")
        result = await session.call_tool(
            "search_patients", arguments={"search_term": "DOE", "limit": 5}
        )
        if result.content and isinstance(result.content[0], TextContent):
            print(
                f"Search result: {json.dumps(result.content[0].text, indent=2)[:500]}..."
            )
        else:
            print("Unexpected response type")

        print("\n" + "=" * 60 + "\n")

        # Test 2: Get patient summary
        print("Test 2: Getting patient summary for DFN 100841...")
        result = await session.call_tool(
            "get_patient_summary", arguments={"patient_dfn": "100841"}
        )
        if result.content and isinstance(result.content[0], TextContent):
            summary = json.loads(result.content[0].text)
        else:
            summary = {"error": "Unexpected response type"}
        if summary.get("success"):
            patient = summary.get("patient", {})
            print(f"Patient: {patient.get('name')} (DFN: {patient.get('dfn')})")
            print(f"Age: {patient.get('age')}, Gender: {patient.get('gender')}")
            # SSN is sensitive data - do not log
            if patient.get("ssn"):
                print("SSN: [MASKED]")
            else:
                print("SSN: [NOT AVAILABLE]")

            clinical = summary.get("clinical_summary", {})
            print(f"\nVitals: {len(clinical.get('vitals', {}))} types")
            print(f"Abnormal labs: {len(clinical.get('abnormal_labs', []))}")
            print(f"Active consults: {len(clinical.get('active_consults', []))}")
        else:
            print(f"Error: {summary.get('error')}")

        print("\n" + "=" * 60 + "\n")

        # Test 3: Get patient vitals
        print("Test 3: Getting patient vitals...")
        result = await session.call_tool(
            "get_patient_vitals",
            arguments={"patient_dfn": "100841", "days_back": 30},
        )
        if result.content and isinstance(result.content[0], TextContent):
            vitals_data = json.loads(result.content[0].text)
        else:
            vitals_data = {"error": "Unexpected response type"}
        if vitals_data.get("success"):
            vitals = vitals_data.get("vitals", {})
            print(f"Total vitals: {vitals.get('count')}")
            print("Latest vitals:")
            for vtype, vdata in vitals.get("latest", {}).items():
                print(f"  - {vtype}: {vdata.get('value')} ({vdata.get('date')})")
        else:
            print(f"Error: {vitals_data.get('error')}")

        print("\n" + "=" * 60 + "\n")

        # Test 4: Get patient labs
        print("Test 4: Getting patient labs (abnormal only)...")
        result = await session.call_tool(
            "get_patient_labs",
            arguments={
                "patient_dfn": "100841",
                "abnormal_only": True,
                "days_back": 90,
            },
        )
        if result.content and isinstance(result.content[0], TextContent):
            labs_data = json.loads(result.content[0].text)
        else:
            labs_data = {"error": "Unexpected response type"}
        if labs_data.get("success"):
            labs = labs_data.get("labs", {})
            print(f"Total labs: {labs.get('count')}")
            print(f"Abnormal: {labs.get('abnormal_count')}")
            print(f"Critical: {labs.get('critical_count')}")

            # Show first few abnormal labs
            all_results = labs.get("all_results", [])
            if all_results:
                print("\nFirst 3 abnormal results:")
                for lab in all_results[:3]:
                    print(
                        f"  - {lab.get('test')}: {lab.get('value')} ({lab.get('interpretation')})"
                    )
        else:
            print(f"Error: {labs_data.get('error')}")

        print("\n" + "=" * 60 + "\n")

        # Test 5: Get patient consults
        print("Test 5: Getting patient consults...")
        result = await session.call_tool(
            "get_patient_consults",
            arguments={"patient_dfn": "100841", "active_only": True},
        )
        if result.content and isinstance(result.content[0], TextContent):
            consults_data = json.loads(result.content[0].text)
        else:
            consults_data = {"error": "Unexpected response type"}
        if consults_data.get("success"):
            consults = consults_data.get("consults", {})
            print(f"Total consults: {consults.get('total')}")
            print(f"Active: {consults.get('active')}")
            print(f"Overdue: {consults.get('overdue')}")

            overdue_list = consults.get("overdue_list", [])
            if overdue_list:
                print("\nOverdue consults:")
                for consult in overdue_list:
                    print(
                        f"  - {consult.get('service')} ({consult.get('urgency')}) - {consult.get('days_overdue')} days overdue"
                    )
        else:
            print(f"Error: {consults_data.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_patient_tools())
