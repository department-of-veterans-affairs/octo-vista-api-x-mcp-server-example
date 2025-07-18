"""Tests for filter utilities"""

from datetime import datetime

from src.filters import (
    ConsultFilter,
    DateRangeFilter,
    LabFilter,
    VitalFilter,
    filter_abnormal_labs,
    filter_consults_by_status,
    filter_labs_by_type,
    filter_urgent_consults,
    get_latest_vital,
)
from src.models.patient.base import (
    ConsultStatus,
    InterpretationCode,
    Urgency,
    VitalType,
)
from src.models.patient.clinical import (
    Consult,
    LabResult,
    VitalSign,
)
from src.models.patient.collection import (
    PatientDataCollection,
)
from src.models.patient.demographics import Demographics


class TestDateRangeFilter:
    """Test date range filter"""

    def test_filter_by_start_date(self):
        """Test filtering by start date only"""
        vitals = [
            VitalSign(
                vital_type=VitalType.BP, value="120/80", datetime=datetime(2024, 1, 1)
            ),
            VitalSign(
                vital_type=VitalType.BP, value="130/85", datetime=datetime(2024, 1, 15)
            ),
            VitalSign(
                vital_type=VitalType.BP, value="125/82", datetime=datetime(2024, 2, 1)
            ),
        ]

        filter = DateRangeFilter(start_date=datetime(2024, 1, 15))
        filtered = filter.filter(vitals)

        assert len(filtered) == 2
        assert filtered[0].value == "130/85"
        assert filtered[1].value == "125/82"

    def test_filter_collection(self):
        """Test filtering entire patient data collection"""
        demographics = Demographics(
            name="TEST,PATIENT",
            ssn="666001234",
            date_of_birth=datetime(1980, 1, 1).date(),
        )

        collection = PatientDataCollection(
            demographics=demographics,
            vitals=[
                VitalSign(
                    vital_type=VitalType.BP,
                    value="120/80",
                    datetime=datetime(2024, 1, 1),
                ),
                VitalSign(
                    vital_type=VitalType.BP,
                    value="130/85",
                    datetime=datetime(2024, 2, 1),
                ),
            ],
            labs=[
                LabResult(
                    test_name="Glucose", value="95", datetime=datetime(2024, 1, 15)
                ),
                LabResult(
                    test_name="Glucose", value="105", datetime=datetime(2024, 2, 15)
                ),
            ],
        )

        filter = DateRangeFilter(start_date=datetime(2024, 2, 1))
        filtered = filter.filter_collection(collection)

        assert filtered.demographics == demographics
        assert len(filtered.vitals) == 1
        assert filtered.vitals[0].value == "130/85"
        assert len(filtered.labs) == 1
        assert filtered.labs[0].value == "105"


class TestLabFilter:
    """Test lab result filters"""

    def test_filter_by_test_name(self):
        """Test filtering by test name"""
        labs = [
            LabResult(test_name="Glucose", value="95"),
            LabResult(test_name="Hemoglobin", value="14.5"),
            LabResult(test_name="Glucose", value="105"),
        ]

        filter = LabFilter(test_name="glucose")
        filtered = filter.filter(labs)

        assert len(filtered) == 2
        assert all(lab.test_name == "Glucose" for lab in filtered)

    def test_filter_abnormal_only(self):
        """Test filtering abnormal results"""
        labs = [
            LabResult(
                test_name="Glucose",
                value="95",
                interpretation_code=InterpretationCode.NORMAL,
            ),
            LabResult(
                test_name="Glucose",
                value="250",
                interpretation_code=InterpretationCode.HIGH,
            ),
            LabResult(
                test_name="Potassium",
                value="6.5",
                interpretation_code=InterpretationCode.CRITICAL_HIGH,
            ),
        ]

        filter = LabFilter(abnormal_only=True)
        filtered = filter.filter(labs)

        assert len(filtered) == 2
        assert all(lab.is_abnormal for lab in filtered)

    def test_filter_critical_only(self):
        """Test filtering critical results"""
        labs = [
            LabResult(
                test_name="Glucose",
                value="95",
                interpretation_code=InterpretationCode.NORMAL,
            ),
            LabResult(
                test_name="Glucose",
                value="250",
                interpretation_code=InterpretationCode.HIGH,
            ),
            LabResult(
                test_name="Potassium",
                value="6.5",
                interpretation_code=InterpretationCode.CRITICAL_HIGH,
            ),
        ]

        filter = LabFilter(critical_only=True)
        filtered = filter.filter(labs)

        assert len(filtered) == 1
        assert filtered[0].interpretation_code == InterpretationCode.CRITICAL_HIGH

    def test_convenience_functions(self):
        """Test convenience filter functions"""
        labs = [
            LabResult(
                test_name="Glucose",
                value="95",
                interpretation_code=InterpretationCode.NORMAL,
            ),
            LabResult(
                test_name="Hemoglobin",
                value="18",
                interpretation_code=InterpretationCode.HIGH,
            ),
            LabResult(
                test_name="Glucose",
                value="450",
                interpretation_code=InterpretationCode.CRITICAL_HIGH,
            ),
        ]

        # Test filter_abnormal_labs
        abnormal = filter_abnormal_labs(labs)
        assert len(abnormal) == 2

        # Test filter_labs_by_type
        glucose_labs = filter_labs_by_type(labs, "Glucose")
        assert len(glucose_labs) == 2


class TestVitalFilter:
    """Test vital sign filters"""

    def test_filter_by_type(self):
        """Test filtering by vital type"""
        vitals = [
            VitalSign(vital_type=VitalType.BP, value="120/80"),
            VitalSign(vital_type=VitalType.TEMP, value="98.6"),
            VitalSign(vital_type=VitalType.BP, value="130/85"),
        ]

        filter = VitalFilter(vital_type=VitalType.BP)
        filtered = filter.filter(vitals)

        assert len(filtered) == 2
        assert all(v.vital_type == VitalType.BP for v in filtered)

    def test_get_latest_vital(self):
        """Test getting latest vital"""
        vitals = [
            VitalSign(
                vital_type=VitalType.BP, value="130/85", datetime=datetime(2024, 1, 14)
            ),
            VitalSign(
                vital_type=VitalType.BP, value="120/80", datetime=datetime(2024, 1, 15)
            ),
            VitalSign(
                vital_type=VitalType.TEMP, value="98.6", datetime=datetime(2024, 1, 15)
            ),
        ]

        # Get latest BP
        latest_bp = get_latest_vital(vitals, VitalType.BP)
        assert latest_bp.value == "120/80"

        # Get latest of any type
        latest = get_latest_vital(vitals)
        assert latest.datetime == datetime(2024, 1, 15)


class TestConsultFilter:
    """Test consult filters"""

    def test_filter_by_status(self):
        """Test filtering by status"""
        consults = [
            Consult(service="Cardiology", status=ConsultStatus.PENDING),
            Consult(service="Neurology", status=ConsultStatus.ACTIVE),
            Consult(service="Cardiology", status=ConsultStatus.COMPLETED),
        ]

        filter = ConsultFilter(status=ConsultStatus.PENDING)
        filtered = filter.filter(consults)

        assert len(filtered) == 1
        assert filtered[0].status == ConsultStatus.PENDING

    def test_filter_by_urgency(self):
        """Test filtering by urgency"""
        consults = [
            Consult(service="Cardiology", urgency=Urgency.ROUTINE),
            Consult(service="Neurology", urgency=Urgency.STAT),
            Consult(service="Cardiology", urgency=Urgency.URGENT),
        ]

        filter = ConsultFilter(urgency=Urgency.STAT)
        filtered = filter.filter(consults)

        assert len(filtered) == 1
        assert filtered[0].urgency == Urgency.STAT

    def test_filter_by_service(self):
        """Test filtering by service"""
        consults = [
            Consult(service="Cardiology"),
            Consult(service="Neurology"),
            Consult(service="Cardiology Clinic"),
        ]

        filter = ConsultFilter(service="cardio")
        filtered = filter.filter(consults)

        assert len(filtered) == 2
        assert all("Cardio" in c.service for c in filtered)

    def test_convenience_functions(self):
        """Test convenience filter functions"""
        consults = [
            Consult(
                service="Cardiology",
                status=ConsultStatus.PENDING,
                urgency=Urgency.ROUTINE,
            ),
            Consult(
                service="Neurology", status=ConsultStatus.ACTIVE, urgency=Urgency.STAT
            ),
            Consult(
                service="Cardiology",
                status=ConsultStatus.PENDING,
                urgency=Urgency.URGENT,
            ),
        ]

        # Test filter_consults_by_status
        pending = filter_consults_by_status(consults, ConsultStatus.PENDING)
        assert len(pending) == 2

        # Test filter_urgent_consults
        urgent = filter_urgent_consults(consults)
        assert len(urgent) == 1
        assert urgent[0].urgency == Urgency.STAT
