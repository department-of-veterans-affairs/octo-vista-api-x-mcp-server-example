"""Tests for patient data models"""

from datetime import datetime

from src.models.patient.base import (
    CodedValue,
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
from src.models.patient.demographics import (
    Address,
    Demographics,
)


class TestCodedValue:
    """Test CodedValue model"""

    def test_from_code_name_pair(self):
        """Test creating from code and name"""
        result = CodedValue.from_code_name_pair("123", "Test Item")
        assert result.code == "123"
        assert result.name == "Test Item"
        assert result.system is None

    def test_with_system(self):
        """Test creating with system"""
        result = CodedValue.from_code_name_pair("123", "Test Item", "test-system")
        assert result.code == "123"
        assert result.name == "Test Item"
        assert result.system == "test-system"


class TestAddress:
    """Test Address model"""

    def test_address_creation(self):
        """Test creating address"""
        address = Address(
            street_address1="123 Main St",
            city="Boston",
            state="MA",
            postal_code="02101",
            country="USA",
        )
        assert address.street_address1 == "123 Main St"
        assert address.city == "Boston"
        assert address.postal_code == "02101"

    def test_address_numeric_postal_code(self):
        """Test address with numeric postal code"""
        address = Address(postal_code=12345)
        assert address.postal_code == "12345"


class TestDemographics:
    """Test Demographics model"""

    def test_demographics_creation(self):
        """Test creating demographics"""
        demographics = Demographics(
            name="SMITH,JOHN",
            ssn="123456789",
            date_of_birth=datetime(1980, 1, 1).date(),
            gender_code="M",
        )
        assert demographics.name == "SMITH,JOHN"
        assert demographics.formatted_ssn == "123-45-6789"
        assert demographics.date_of_birth.year == 1980

    def test_ssn_formatting(self):
        """Test SSN formatting"""
        demographics = Demographics(
            name="TEST", ssn="666001234", date_of_birth=datetime(1980, 1, 1).date()
        )
        assert demographics.formatted_ssn == "666-00-1234"


class TestVitalSign:
    """Test VitalSign model"""

    def test_vital_sign_blood_pressure(self):
        """Test blood pressure vital sign"""
        vital = VitalSign(
            uid="vital-1",
            local_id="123",
            type_code="8480-6",
            type_name="BLOOD PRESSURE",
            display_name="Blood Pressure",
            result="120/80",
            observed=datetime(2024, 1, 15, 14, 30),
            resulted=datetime(2024, 1, 15, 14, 30),
            facility_code="500",
            facility_name="Test Hospital",
        )
        assert vital.vital_type == VitalType.BP
        assert vital.result == "120/80"
        assert vital.systolic == 120
        assert vital.diastolic == 80

    def test_vital_sign_temperature(self):
        """Test temperature vital sign"""
        vital = VitalSign(
            uid="vital-2",
            local_id="124",
            type_code="8310-5",
            type_name="TEMPERATURE",
            display_name="Temperature",
            result="98.6",
            units="F",
            observed=datetime(2024, 1, 15, 14, 30),
            resulted=datetime(2024, 1, 15, 14, 30),
            facility_code="500",
            facility_name="Test Hospital",
        )
        assert vital.vital_type == VitalType.TEMP
        assert vital.numeric_result == 98.6


class TestLabResult:
    """Test LabResult model"""

    def test_lab_result_normal(self):
        """Test normal lab result"""
        lab = LabResult(
            uid="lab-1",
            local_id="125",
            type_code="2345-7",
            type_name="GLUCOSE",
            display_name="Glucose",
            result="95",
            units="mg/dL",
            low="70",
            high="100",
            interpretation_code="N",
            observed=datetime(2024, 1, 15),
            resulted=datetime(2024, 1, 15),
            verified=datetime(2024, 1, 15),
            facility_code="500",
            facility_name="Test Hospital",
        )
        assert lab.type_name == "GLUCOSE"
        assert lab.numeric_result == 95.0
        assert not lab.is_abnormal

    def test_lab_result_abnormal(self):
        """Test abnormal lab result"""
        lab = LabResult(
            uid="lab-2",
            local_id="126",
            type_code="2345-7",
            type_name="GLUCOSE",
            display_name="Glucose",
            result="250",
            units="mg/dL",
            low="70",
            high="100",
            interpretation_code="H",
            observed=datetime(2024, 1, 15),
            resulted=datetime(2024, 1, 15),
            verified=datetime(2024, 1, 15),
            facility_code="500",
            facility_name="Test Hospital",
        )
        assert lab.is_abnormal
        assert lab.numeric_result == 250.0

    def test_lab_result_critical(self):
        """Test critical lab result"""
        lab = LabResult(
            uid="lab-3",
            local_id="127",
            type_code="2345-7",
            type_name="GLUCOSE",
            display_name="Glucose",
            result="450",
            interpretation_code="HH",
            observed=datetime(2024, 1, 15),
            resulted=datetime(2024, 1, 15),
            verified=datetime(2024, 1, 15),
            facility_code="500",
            facility_name="Test Hospital",
        )
        assert lab.is_abnormal
        assert lab.interpretation == InterpretationCode.CRITICAL_HIGH


class TestConsult:
    """Test Consult model"""

    def test_consult_creation(self):
        """Test creating consult"""
        consult = Consult(
            service="Cardiology",
            urgency=Urgency.URGENT,
            status=ConsultStatus.PENDING,
            reason="Chest pain evaluation",
            date_time=datetime(2024, 1, 15),
        )
        assert consult.service == "Cardiology"
        assert consult.urgency == Urgency.URGENT
        assert consult.status == ConsultStatus.PENDING

    def test_consult_provisional_dx_parsing(self):
        """Test provisional diagnosis parsing"""
        consult = Consult(
            service="Cardiology",
            provisional_dx=[
                {"code": "I20.9", "name": "Angina pectoris"},
                {"code": "I10", "name": "Essential hypertension"},
            ],
        )
        assert len(consult.provisional_dx) == 2
        assert consult.provisional_dx[0].code == "I20.9"


class TestPatientDataCollection:
    """Test PatientDataCollection model"""

    def test_collection_creation(self):
        """Test creating patient data collection"""
        demographics = Demographics(
            name="TEST,PATIENT",
            ssn="123456789",
            date_of_birth=datetime(1980, 1, 1).date(),
        )

        collection = PatientDataCollection(
            demographics=demographics,
            vitals=[
                VitalSign(vital_type=VitalType.BP, value="120/80"),
                VitalSign(vital_type=VitalType.TEMP, value="98.6"),
            ],
            labs=[LabResult(test_name="Glucose", value="95")],
        )

        assert collection.demographics.name == "TEST,PATIENT"
        assert len(collection.vitals) == 2
        assert len(collection.labs) == 1

    def test_get_latest_vitals(self):
        """Test getting latest vitals by type"""
        demographics = Demographics(
            name="TEST", ssn="123456789", date_of_birth=datetime(1980, 1, 1).date()
        )

        collection = PatientDataCollection(
            demographics=demographics,
            vitals=[
                VitalSign(
                    vital_type=VitalType.BP,
                    value="130/85",
                    datetime=datetime(2024, 1, 14),
                ),
                VitalSign(
                    vital_type=VitalType.BP,
                    value="120/80",
                    datetime=datetime(2024, 1, 15),
                ),
                VitalSign(
                    vital_type=VitalType.TEMP,
                    value="98.6",
                    datetime=datetime(2024, 1, 15),
                ),
            ],
        )

        latest_vitals = collection.get_latest_vitals()
        assert len(latest_vitals) == 2  # One BP and one TEMP

        # Check that we got the latest BP
        bp_vital = next(v for v in latest_vitals if v.vital_type == VitalType.BP)
        assert bp_vital.value == "120/80"

    def test_get_abnormal_labs(self):
        """Test getting abnormal labs"""
        demographics = Demographics(
            name="TEST", ssn="123456789", date_of_birth=datetime(1980, 1, 1).date()
        )

        collection = PatientDataCollection(
            demographics=demographics,
            labs=[
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
            ],
        )

        abnormal = collection.get_abnormal_labs()
        assert len(abnormal) == 2
        assert all(lab.is_abnormal for lab in abnormal)
