"""Test the Treatment model properties and behavior"""

from datetime import datetime

from src.models.patient.treatment import Treatment, TreatmentStatus


def test_treatment_instance_completed_property():
    """Test that Treatment instances properly handle completed status"""

    # Create a treatment with completed status
    treatment_data = {
        "uid": "test-completed-123",
        "dfn": "100024",
        "name": "Completed Treatment",
        "date": datetime.now(),
        "status": "COMPLETE",  # This should be parsed to TreatmentStatus.COMPLETED
    }

    treatment = Treatment(**treatment_data)

    # Test that the status was properly parsed
    assert treatment.status == TreatmentStatus.COMPLETED

    # Test the convenience properties
    assert treatment.is_completed is True
    assert treatment.is_active is False
    assert treatment.is_pending is False
    assert treatment.is_scheduled is False
    assert treatment.is_discontinued is False
    assert treatment.is_expired is False
    assert treatment.is_lapsed is False


def test_treatment_instance_active_property():
    """Test that Treatment instances properly handle active (in-progress) status"""

    # Create a treatment with active status
    treatment_data = {
        "uid": "test-active-123",
        "dfn": "100024",
        "name": "Active Treatment",
        "date": datetime.now(),
        "status": "ACTIVE",  # This should be parsed to TreatmentStatus.IN_PROGRESS
    }

    treatment = Treatment(**treatment_data)

    # Test that the status was properly parsed
    assert treatment.status == TreatmentStatus.IN_PROGRESS

    # Test the convenience properties
    assert treatment.is_active is True
    assert treatment.is_completed is False
    assert treatment.is_pending is False
    assert treatment.is_scheduled is False
    assert treatment.is_discontinued is False
    assert treatment.is_expired is False
    assert treatment.is_lapsed is False


def test_treatment_instance_pending_property():
    """Test that Treatment instances properly handle pending status"""

    # Create a treatment with pending status
    treatment_data = {
        "uid": "test-pending-123",
        "dfn": "100024",
        "name": "Pending Treatment",
        "date": datetime.now(),
        "status": "PENDING",  # This should be parsed to TreatmentStatus.PENDING
    }

    treatment = Treatment(**treatment_data)

    # Test that the status was properly parsed
    assert treatment.status == TreatmentStatus.PENDING

    # Test the convenience properties
    assert treatment.is_pending is True
    assert treatment.is_active is False
    assert treatment.is_completed is False
    assert treatment.is_scheduled is False
    assert treatment.is_discontinued is False
    assert treatment.is_expired is False
    assert treatment.is_lapsed is False


def test_treatment_instance_scheduled_property():
    """Test that Treatment instances properly handle scheduled status"""

    # Create a treatment with scheduled status
    treatment_data = {
        "uid": "test-scheduled-123",
        "dfn": "100024",
        "name": "Scheduled Treatment",
        "date": datetime.now(),
        "status": "SCHEDULED",  # This should be parsed to TreatmentStatus.SCHEDULED
    }

    treatment = Treatment(**treatment_data)

    # Test that the status was properly parsed
    assert treatment.status == TreatmentStatus.SCHEDULED

    # Test the convenience properties
    assert treatment.is_scheduled is True
    assert treatment.is_active is False
    assert treatment.is_completed is False
    assert treatment.is_pending is False
    assert treatment.is_discontinued is False
    assert treatment.is_expired is False
    assert treatment.is_lapsed is False


def test_treatment_instance_discontinued_property():
    """Test that Treatment instances properly handle discontinued status"""

    # Test regular discontinued
    treatment_data = {
        "uid": "test-discontinued-123",
        "dfn": "100024",
        "name": "Discontinued Treatment",
        "date": datetime.now(),
        "status": "DISCONTINUED",
    }

    treatment = Treatment(**treatment_data)
    assert treatment.status == TreatmentStatus.DISCONTINUED
    assert treatment.is_discontinued is True
    assert treatment.is_active is False
    assert treatment.is_completed is False
    assert treatment.is_pending is False
    assert treatment.is_scheduled is False
    assert treatment.is_expired is False
    assert treatment.is_lapsed is False

    # Test edited discontinued
    treatment_data["status"] = "DISCONTINUED/EDIT"
    treatment_edited = Treatment(**treatment_data)
    assert treatment_edited.status == TreatmentStatus.EDITED_DISCONTINUED
    assert treatment_edited.is_discontinued is True


def test_treatment_instance_expired_property():
    """Test that Treatment instances properly handle expired status"""

    treatment_data = {
        "uid": "test-expired-123",
        "dfn": "100024",
        "name": "Expired Treatment",
        "date": datetime.now(),
        "status": "EXPIRED",
    }

    treatment = Treatment(**treatment_data)
    assert treatment.status == TreatmentStatus.EXPIRED
    assert treatment.is_expired is True
    assert treatment.is_active is False
    assert treatment.is_completed is False
    assert treatment.is_pending is False
    assert treatment.is_scheduled is False
    assert treatment.is_discontinued is False
    assert treatment.is_lapsed is False


def test_treatment_instance_lapsed_property():
    """Test that Treatment instances properly handle lapsed status"""

    treatment_data = {
        "uid": "test-lapsed-123",
        "dfn": "100024",
        "name": "Lapsed Treatment",
        "date": datetime.now(),
        "status": "LAPSED",
    }

    treatment = Treatment(**treatment_data)
    assert treatment.status == TreatmentStatus.LAPSED
    assert treatment.is_lapsed is True
    assert treatment.is_active is False
    assert treatment.is_completed is False
    assert treatment.is_pending is False
    assert treatment.is_scheduled is False
    assert treatment.is_discontinued is False
    assert treatment.is_expired is False


def test_treatment_default_status():
    """Test that Treatment has correct default status"""

    # Create a treatment without specifying status
    treatment_data = {
        "uid": "test-default-123",
        "dfn": "100024",
        "name": "Default Treatment",
        "date": datetime.now(),
        # No status specified
    }

    treatment = Treatment(**treatment_data)

    # Should default to PENDING
    assert treatment.status == TreatmentStatus.PENDING
    assert treatment.is_pending is True


def test_treatment_status_parsing():
    """Test that Treatment properly parses status from various input formats"""

    # Test with TreatmentStatus enum value
    treatment_data = {
        "uid": "test-enum-123",
        "dfn": "100024",
        "name": "Enum Status Treatment",
        "date": datetime.now(),
        "status": TreatmentStatus.COMPLETED,
    }

    treatment = Treatment(**treatment_data)
    assert treatment.status == TreatmentStatus.COMPLETED

    # Test with string value
    treatment_data["status"] = "ACTIVE"
    treatment = Treatment(**treatment_data)
    assert treatment.status == TreatmentStatus.IN_PROGRESS
