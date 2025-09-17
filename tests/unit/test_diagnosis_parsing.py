"""Unit tests for diagnosis parsing functionality."""

from src.models.patient.diagnosis import Diagnosis
from src.services.parsers.patient.patient_parser import PatientDataParser
from src.services.validators.clinical_validators import (
    validate_icd_code,
)


class TestDiagnosisModel:
    """Test Diagnosis Pydantic model functionality."""

    def test_diagnosis_creation_with_valid_data(self):
        """Test creating a Diagnosis with valid data."""
        data = {
            "uid": "urn:va:problem:9E7A:100022:1001",
            "localId": "1001",
            "icdCode": "I25.10",
            "icdName": "Atherosclerotic heart disease",
            "facilityCode": "500",
            "facilityName": "SALT LAKE CITY",
            "entered": "20231201",
        }

        diagnosis = Diagnosis(**data)

        assert diagnosis.uid == "urn:va:problem:9E7A:100022:1001"
        assert diagnosis.local_id == "1001"
        assert diagnosis.icd_code == "I25.10"
        assert diagnosis.description == "Atherosclerotic heart disease"
        assert diagnosis.facility_code == "500"
        assert diagnosis.facility_name == "SALT LAKE CITY"

    def test_diagnosis_field_validation(self):
        """Test field validation and defaults."""
        minimal_data = {
            "uid": "test:uid",
            "localId": "123",
            "icdCode": "I25.10",
            "icdName": "Test Diagnosis",
            "facilityCode": "500",
            "facilityName": "Test Facility",
            "entered": "20231201",
        }

        diagnosis = Diagnosis(**minimal_data)

        # Check defaults
        assert diagnosis.status == "active"


class TestICDCodeValidation:
    """Test ICD code validation functionality."""

    def test_valid_icd_10_codes(self):
        """Test validation of valid ICD-10 codes."""
        valid_codes = [
            "A01",
            "B95.1",
            "C78.00",
            "Z51.11",
            "I25.10",
            "J44.1",
            "E11.9",
            "F32.9",
        ]

        for code in valid_codes:
            assert validate_icd_code(code, "ICD-10"), f"Code {code} should be valid"

    def test_valid_icd_9_codes(self):
        """Test validation of valid ICD-9 codes."""
        valid_codes = [
            "250",
            "250.0",
            "401.9",
            "V58.69",
            "E879.3",
            "999.9",
        ]

        for code in valid_codes:
            assert validate_icd_code(code, "ICD-9"), f"Code {code} should be valid"

    def test_invalid_icd_codes(self):
        """Test validation of invalid ICD codes."""
        invalid_cases = [
            ("INVALID", "ICD-10"),
            ("", "ICD-10"),
            ("12345", "ICD-10"),
            ("A", "ICD-10"),
            ("", "ICD-9"),
            ("12", "ICD-9"),
            ("ABCD", "ICD-9"),
        ]

        for code, version in invalid_cases:
            assert not validate_icd_code(
                code, version
            ), f"Code {code} should be invalid"

    def test_empty_or_none_inputs(self):
        """Test validation with empty or None inputs."""
        assert not validate_icd_code("", "ICD-10")
        assert not validate_icd_code("A01", "")
        assert not validate_icd_code(None, "ICD-10")


class TestDiagnosisParser:
    """Test diagnosis parsing functionality."""

    def test_preprocess_diagnosis_item(self):
        """Test diagnosis item preprocessing."""
        parser = PatientDataParser("500", "123")

        # Test with minimal data
        minimal_item = {
            "uid": "urn:va:problem:9E7A:100022:1001",
            "icdCode": "I25.10",
            "icdName": "Coronary Disease",
        }

        processed = parser._preprocess_diagnosis_item(minimal_item)

        # Check defaults were added
        assert "localId" in processed
        assert "facilityCode" in processed
        assert "facilityName" in processed
        assert "entered" in processed

    def test_parse_diagnoses(self):
        """Test full diagnosis parsing."""
        parser = PatientDataParser("500", "123")

        problem_items = [
            {
                "uid": "urn:va:problem:9E7A:100022:1001",
                "localId": "1001",
                "icdCode": "I25.10",
                "icdName": "Atherosclerotic heart disease",
                "facilityCode": "500",
                "facilityName": "SALT LAKE CITY",
                "entered": "20231201",
            },
            {
                "uid": "urn:va:problem:9E7A:100022:1002",
                "localId": "1002",
                "icdCode": "E11.9",
                "icdName": "Type 2 diabetes",
                "facilityCode": "500",
                "facilityName": "SALT LAKE CITY",
                "entered": "20231215",
            },
        ]

        diagnoses = parser._parse_diagnoses(problem_items)

        # Now returns dict keyed by UID
        assert isinstance(diagnoses, dict)
        assert len(diagnoses) == 2

        # Convert to list and sort by diagnosis_date desc to assert order
        dx_list = list(diagnoses.values())
        dx_list.sort(key=lambda d: d.diagnosis_date, reverse=True)

        # Check first diagnosis (newest)
        first_dx = dx_list[0]
        assert first_dx.icd_code == "E11.9"
        assert first_dx.description == "Type 2 diabetes"

        # Check second diagnosis
        second_dx = dx_list[1]
        assert second_dx.icd_code == "I25.10"
        assert second_dx.description == "Atherosclerotic heart disease"
