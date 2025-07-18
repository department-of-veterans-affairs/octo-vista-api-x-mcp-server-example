#!/usr/bin/env python
# mypy: ignore-errors
"""Test the mock server's VPR RPC directly"""

import sys
from pathlib import Path

# Add mock_server to path
sys.path.insert(0, str(Path(__file__).parent / "mock_server" / "src"))

from rpc.handlers.patient_handlers import PatientHandlers
from rpc.models import Parameter


def test_vpr_rpc():
    """Test VPR GET PATIENT DATA JSON handler directly"""

    print("Testing VPR GET PATIENT DATA JSON handler...")

    # Test 1: Named array format (production format)
    print("\n1. Testing with named array format:")
    parameters = [Parameter(namedArray={"patientId": "100841"})]

    result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

    if isinstance(result, dict):
        if "error" in result:
            print(f"   Error: {result['error']}")
        else:
            items = result.get("data", {}).get("items", [])
            print(f"   Success! Got {len(items)} items")

            # Count by type
            types: dict[str, int] = {}
            for item in items:
                uid = item.get("uid", "")
                if ":" in uid:
                    item_type = uid.split(":")[2]
                    types[item_type] = types.get(item_type, 0) + 1

            print("   Item types:")
            for item_type, count in sorted(types.items()):
                print(f"     - {item_type}: {count}")

            # Show patient demographics
            patient_items = [i for i in items if ":patient:" in i.get("uid", "")]
            if patient_items:
                patient = patient_items[0]
                print("\n   Patient info:")
                print(f"     - Name: {patient.get('fullName')}")
                print(f"     - DFN: {patient.get('localId')}")
                print(f"     - ICN: {patient.get('icn')}")
                # DOB is sensitive data - do not log
                if patient.get("dateOfBirth"):
                    print("     - DOB: [MASKED]")
                else:
                    print("     - DOB: [NOT AVAILABLE]")
                print(f"     - Gender: {patient.get('genderName')}")

    # Test 2: Legacy string format
    print("\n2. Testing with legacy string format:")
    parameters = [
        Parameter(string="100841"),
        Parameter(string=""),
        Parameter(string=""),
        Parameter(string="patient;vital;lab"),
    ]

    result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

    if isinstance(result, dict):
        if "error" in result:
            print(f"   Error: {result['error']}")
        else:
            items = result.get("data", {}).get("items", [])
            print(f"   Success! Got {len(items)} items")

    # Test 3: Non-existent patient
    print("\n3. Testing with non-existent patient:")
    parameters = [Parameter(namedArray={"patientId": "999999"})]

    result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

    if isinstance(result, dict):
        if "error" in result:
            print(f"   Expected error: {result['error']}")
        else:
            print("   Unexpected success!")

    # Test 4: Verify data structure
    print("\n4. Verifying data structure for patient 100841:")
    parameters = [Parameter(namedArray={"patientId": "100841"})]

    result = PatientHandlers.handle_vpr_get_patient_data_json(parameters)

    if isinstance(result, dict) and "data" in result:
        items = result.get("data", {}).get("items", [])

        # Check vital signs
        vitals = [i for i in items if ":vital:" in i.get("uid", "")]
        if vitals:
            print("\n   Sample vital sign:")
            vital = vitals[0]
            print(f"     - Type: {vital.get('typeName')}")
            print(f"     - Value: {vital.get('result')} {vital.get('units', '')}")
            print(f"     - Date: {vital.get('observed')}")

        # Check lab results
        labs = [i for i in items if ":lab:" in i.get("uid", "")]
        if labs:
            print("\n   Sample lab result:")
            lab = labs[0]
            print(f"     - Test: {lab.get('typeName')}")
            print(f"     - Value: {lab.get('result')} {lab.get('units', '')}")
            print(f"     - Status: {lab.get('interpretationName', 'Normal')}")

        # Check consults
        consults = [i for i in items if ":consult:" in i.get("uid", "")]
        if consults:
            print("\n   Sample consult:")
            consult = consults[0]
            print(f"     - Service: {consult.get('service')}")
            print(f"     - Status: {consult.get('statusName')}")
            print(f"     - Urgency: {consult.get('urgency')}")


if __name__ == "__main__":
    test_vpr_rpc()
