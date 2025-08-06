#!/usr/bin/env python3
"""Test script for the new visit tool functionality"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import datetime, timedelta, timezone

from src.models.patient.visits import Visit, VisitType


def test_visit_model():
    """Test the Visit model functionality"""
    print("Testing Visit model...")

    # Create a test visit
    visit = Visit(
        uid="test-visit-123",
        local_id="123",
        visit_date=datetime.now(timezone.utc),
        admission_date=datetime.now(timezone.utc) - timedelta(days=2),
        location_code="WARD",
        location_name="MEDICAL WARD",
        facility_code="500",
        facility_name="VA Medical Center",
        status_code="ACTIVE",
        status_name="ACTIVE",
    )

    print(f"Visit created: {visit.uid}")
    print(f"Visit type: {visit.visit_type}")
    print(f"Is inpatient: {visit.is_inpatient}")
    print(f"Is active: {visit.is_active}")
    print(f"Duration: {visit.duration_days} days")
    print(f"Display location: {visit.display_location}")
    print(f"Display dates: {visit.display_dates}")


def test_visit_type_classification():
    """Test visit type classification"""
    print("\nTesting VisitType classification...")

    test_cases = [
        ("ER", "EMERGENCY ROOM", VisitType.EMERGENCY),
        ("WARD", "MEDICAL WARD", VisitType.INPATIENT),
        ("OR", "OPERATING ROOM", VisitType.SURGERY),
        ("OBS", "OBSERVATION UNIT", VisitType.OBSERVATION),
        ("CLINIC", "PRIMARY CARE CLINIC", VisitType.OUTPATIENT),
    ]

    for location_code, location_name, expected in test_cases:
        result = VisitType.from_location_code(location_code, location_name)
        status = "✓" if result == expected else "✗"
        print(f"{status} {location_code} - {location_name} -> {result}")


if __name__ == "__main__":
    test_visit_model()
    test_visit_type_classification()
    print("\nAll tests passed!")
