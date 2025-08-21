"""Test the TreatmentStatus enum mapping and methods"""

from src.models.patient.treatment import TreatmentStatus


def test_treatment_status_completed_mapping():
    """Test that COMPLETED/COMPLETE status is properly mapped from external values"""

    # Test direct mapping from external values
    assert TreatmentStatus.from_external_value("COMPLETED") == TreatmentStatus.COMPLETED
    assert TreatmentStatus.from_external_value("COMPLETE") == TreatmentStatus.COMPLETED
    assert TreatmentStatus.from_external_value("completed") == TreatmentStatus.COMPLETED
    assert TreatmentStatus.from_external_value("complete") == TreatmentStatus.COMPLETED

    # Test the is_completed class method
    assert TreatmentStatus.is_completed(TreatmentStatus.COMPLETED) is True
    assert TreatmentStatus.is_completed(TreatmentStatus.IN_PROGRESS) is False
    assert TreatmentStatus.is_completed(TreatmentStatus.PENDING) is False


def test_treatment_status_active_mapping():
    """Test that ACTIVE status is properly mapped to IN_PROGRESS"""

    # Test direct mapping from external values
    assert TreatmentStatus.from_external_value("ACTIVE") == TreatmentStatus.IN_PROGRESS
    assert TreatmentStatus.from_external_value("active") == TreatmentStatus.IN_PROGRESS
    assert (
        TreatmentStatus.from_external_value("IN_PROGRESS")
        == TreatmentStatus.IN_PROGRESS
    )
    assert (
        TreatmentStatus.from_external_value("IN-PROGRESS")
        == TreatmentStatus.IN_PROGRESS
    )

    # Test the is_active class method
    assert TreatmentStatus.is_active(TreatmentStatus.IN_PROGRESS) is True
    assert TreatmentStatus.is_active(TreatmentStatus.COMPLETED) is False
    assert TreatmentStatus.is_active(TreatmentStatus.PENDING) is False


def test_treatment_status_pending_mapping():
    """Test that PENDING status is properly mapped from external values"""

    # Test direct mapping from external values
    assert TreatmentStatus.from_external_value("PENDING") == TreatmentStatus.PENDING
    assert TreatmentStatus.from_external_value("pending") == TreatmentStatus.PENDING

    # Test the is_pending class method
    assert TreatmentStatus.is_pending(TreatmentStatus.PENDING) is True
    assert TreatmentStatus.is_pending(TreatmentStatus.COMPLETED) is False
    assert TreatmentStatus.is_pending(TreatmentStatus.IN_PROGRESS) is False
    assert TreatmentStatus.is_pending(TreatmentStatus.SCHEDULED) is False


def test_treatment_status_scheduled_mapping():
    """Test that SCHEDULED status is properly mapped from external values"""

    # Test direct mapping from external values
    assert TreatmentStatus.from_external_value("SCHEDULED") == TreatmentStatus.SCHEDULED
    assert TreatmentStatus.from_external_value("scheduled") == TreatmentStatus.SCHEDULED

    # Test the is_scheduled class method
    assert TreatmentStatus.is_scheduled(TreatmentStatus.SCHEDULED) is True
    assert TreatmentStatus.is_scheduled(TreatmentStatus.COMPLETED) is False
    assert TreatmentStatus.is_scheduled(TreatmentStatus.IN_PROGRESS) is False
    assert TreatmentStatus.is_scheduled(TreatmentStatus.PENDING) is False


def test_treatment_status_discontinued_mapping():
    """Test that DISCONTINUED status is properly mapped from external values"""

    # Test direct mapping from external values
    assert (
        TreatmentStatus.from_external_value("DISCONTINUED")
        == TreatmentStatus.DISCONTINUED
    )
    assert (
        TreatmentStatus.from_external_value("discontinued")
        == TreatmentStatus.DISCONTINUED
    )

    # Test the is_discontinued class method
    assert TreatmentStatus.is_discontinued(TreatmentStatus.DISCONTINUED) is True
    assert TreatmentStatus.is_discontinued(TreatmentStatus.EDITED_DISCONTINUED) is True
    assert TreatmentStatus.is_discontinued(TreatmentStatus.COMPLETED) is False


def test_treatment_status_edited_discontinued_mapping():
    """Test that DISCONTINUED/EDIT status is properly mapped to EDITED_DISCONTINUED"""

    # Test direct mapping from external values
    assert (
        TreatmentStatus.from_external_value("DISCONTINUED/EDIT")
        == TreatmentStatus.EDITED_DISCONTINUED
    )

    # Test the is_discontinued class method includes edited discontinued
    assert TreatmentStatus.is_discontinued(TreatmentStatus.EDITED_DISCONTINUED) is True


def test_treatment_status_expired_mapping():
    """Test that EXPIRED status is properly mapped from external values"""

    # Test direct mapping from external values
    assert TreatmentStatus.from_external_value("EXPIRED") == TreatmentStatus.EXPIRED
    assert TreatmentStatus.from_external_value("expired") == TreatmentStatus.EXPIRED

    # Test the is_expired class method
    assert TreatmentStatus.is_expired(TreatmentStatus.EXPIRED) is True
    assert TreatmentStatus.is_expired(TreatmentStatus.COMPLETED) is False


def test_treatment_status_lapsed_mapping():
    """Test that LAPSED status is properly mapped from external values"""

    # Test direct mapping from external values
    assert TreatmentStatus.from_external_value("LAPSED") == TreatmentStatus.LAPSED
    assert TreatmentStatus.from_external_value("lapsed") == TreatmentStatus.LAPSED

    # Test the is_lapsed class method
    assert TreatmentStatus.is_lapsed(TreatmentStatus.LAPSED) is True
    assert TreatmentStatus.is_lapsed(TreatmentStatus.COMPLETED) is False


def test_treatment_status_unknown_fallback():
    """Test that unknown status values fall back to PENDING"""

    # Test unknown values fall back to PENDING
    assert TreatmentStatus.from_external_value("UNKNOWN") == TreatmentStatus.PENDING
    assert TreatmentStatus.from_external_value("") == TreatmentStatus.PENDING
    assert TreatmentStatus.from_external_value(None) == TreatmentStatus.PENDING
    assert (
        TreatmentStatus.from_external_value("RANDOM_VALUE") == TreatmentStatus.PENDING
    )


def test_treatment_status_values():
    """Test that all expected status values are available"""

    # Test that all statuses are in the enum
    assert hasattr(TreatmentStatus, "COMPLETED")
    assert hasattr(TreatmentStatus, "IN_PROGRESS")
    assert hasattr(TreatmentStatus, "PENDING")
    assert hasattr(TreatmentStatus, "SCHEDULED")
    assert hasattr(TreatmentStatus, "DISCONTINUED")
    assert hasattr(TreatmentStatus, "EXPIRED")
    assert hasattr(TreatmentStatus, "LAPSED")
    assert hasattr(TreatmentStatus, "EDITED_DISCONTINUED")

    # Test enum values
    assert TreatmentStatus.COMPLETED == "completed"
    assert TreatmentStatus.IN_PROGRESS == "in-progress"
    assert TreatmentStatus.PENDING == "pending"
    assert TreatmentStatus.SCHEDULED == "scheduled"
    assert TreatmentStatus.DISCONTINUED == "discontinued"
    assert TreatmentStatus.EXPIRED == "expired"
    assert TreatmentStatus.LAPSED == "lapsed"
    assert TreatmentStatus.EDITED_DISCONTINUED == "edited-discontinued"

    # Test that all expected values exist
    expected_statuses = [
        "completed",
        "in-progress",
        "pending",
        "scheduled",
        "discontinued",
        "expired",
        "lapsed",
        "edited-discontinued",
    ]
    actual_statuses = [status.value for status in TreatmentStatus]

    for expected in expected_statuses:
        assert expected in actual_statuses


def test_treatment_status_removed_values():
    """Test that removed status values are not in the enum"""

    # Test that CANCELLED and PLANNED were removed
    assert not hasattr(TreatmentStatus, "CANCELLED")
    assert not hasattr(TreatmentStatus, "PLANNED")

    # Test that removed values fall back to PENDING
    assert TreatmentStatus.from_external_value("CANCELLED") == TreatmentStatus.PENDING
    assert TreatmentStatus.from_external_value("CANCELED") == TreatmentStatus.PENDING
    assert TreatmentStatus.from_external_value("PLANNED") == TreatmentStatus.PENDING
