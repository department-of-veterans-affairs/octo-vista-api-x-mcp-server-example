"""Unit tests for CPT code parsing and validation"""

from datetime import UTC, datetime

import pytest

from src.models.patient.cpt_code import CPTCode
from src.services.validators.cpt_validators import (
    categorize_cpt_code,
    get_procedure_complexity,
    parse_cpt_modifiers,
    validate_cpt_code,
)


class TestCPTCodeModel:
    """Test CPT code model functionality"""

    def test_cpt_code_creation(self):
        """Test basic CPT code model creation"""
        data = {
            "uid": "urn:va:cpt:84F0:237:5326",
            "localId": "5326",
            "cptCode": "urn:cpt:82950",
            "name": "Glucose",
            "dateTime": "20240101120000",
            "facilityCode": "500",
            "facilityName": "Test Hospital",
        }

        cpt = CPTCode(**data)

        assert cpt.uid == "urn:va:cpt:84F0:237:5326"
        assert cpt.local_id == "5326"
        assert cpt.cpt_code == "82950"  # Should strip URN prefix
        assert cpt.description == "Glucose"
        assert isinstance(cpt.procedure_date, datetime)
        assert cpt.facility_code == "500"
        assert cpt.facility_name == "Test Hospital"

    def test_cpt_code_normalization(self):
        """Test CPT code URN normalization"""
        data = {
            "uid": "urn:va:cpt:84F0:237:5326",
            "localId": "5326",
            "cptCode": "urn:cpt:99213",
            "name": "Office Visit",
            "dateTime": "20240101120000",
            "facilityCode": "500",
            "facilityName": "Test Hospital",
        }

        cpt = CPTCode(**data)
        assert cpt.cpt_code == "99213"

    def test_modifiers_parsing(self):
        """Test CPT modifiers parsing"""
        data = {
            "uid": "urn:va:cpt:84F0:237:5326",
            "localId": "5326",
            "cptCode": "99213",
            "name": "Office Visit",
            "dateTime": "20240101120000",
            "facilityCode": "500",
            "facilityName": "Test Hospital",
            "modifiers": "25,59",
        }

        cpt = CPTCode(**data)
        assert cpt.modifiers == ["25", "59"]
        assert cpt.has_modifiers is True

    def test_procedure_properties(self):
        """Test computed properties"""
        # Surgery code
        surgery_data = {
            "uid": "urn:va:cpt:84F0:237:5326",
            "localId": "5326",
            "cptCode": "12345",  # Surgery range
            "name": "Surgical Procedure",
            "dateTime": "20240101120000",
            "facilityCode": "500",
            "facilityName": "Test Hospital",
        }

        surgery_cpt = CPTCode(**surgery_data)
        assert surgery_cpt.is_surgical is True
        assert surgery_cpt.is_diagnostic is False
        assert surgery_cpt.procedure_category == "surgery"

        # Radiology code
        radiology_data = surgery_data.copy()
        radiology_data["cptCode"] = "71020"  # Radiology range
        radiology_data["name"] = "Chest X-ray"

        radiology_cpt = CPTCode(**radiology_data)
        assert radiology_cpt.is_surgical is False
        assert radiology_cpt.is_diagnostic is True
        assert radiology_cpt.procedure_category == "radiology"


class TestCPTValidators:
    """Test CPT validation functions"""

    def test_validate_cpt_code(self):
        """Test CPT code format validation"""
        # Valid codes
        assert validate_cpt_code("99213") is True
        assert validate_cpt_code("12345") is True
        assert validate_cpt_code("0001F") is True  # Category II

        # Invalid codes
        assert validate_cpt_code("") is False
        assert validate_cpt_code("123") is False  # Too short
        assert validate_cpt_code("123456") is False  # Too long
        assert validate_cpt_code("ABCDE") is False  # All letters
        assert validate_cpt_code(None) is False

    def test_categorize_cpt_code(self):
        """Test CPT code categorization"""
        # Surgery codes
        assert categorize_cpt_code("12345") == "surgery"
        assert categorize_cpt_code("55555") == "surgery"

        # Radiology codes
        assert categorize_cpt_code("71020") == "radiology"
        assert categorize_cpt_code("75000") == "radiology"

        # Pathology codes
        assert categorize_cpt_code("82950") == "pathology"
        assert categorize_cpt_code("85025") == "pathology"

        # E&M codes
        assert categorize_cpt_code("99213") == "evaluation"
        assert categorize_cpt_code("99282") == "evaluation"

        # Unknown codes
        assert categorize_cpt_code("") == "unknown"
        assert categorize_cpt_code("invalid") == "unknown"

    def test_categorize_with_description(self):
        """Test categorization with description context"""
        # Description overrides code range
        assert categorize_cpt_code("99999", "surgical procedure") == "surgery"
        assert categorize_cpt_code("99999", "x-ray imaging") == "radiology"
        assert categorize_cpt_code("99999", "lab test") == "pathology"

    def test_parse_cpt_modifiers(self):
        """Test CPT modifier parsing"""
        # Comma separated
        assert parse_cpt_modifiers("25,59") == ["25", "59"]

        # Space separated
        assert parse_cpt_modifiers("25 59") == ["25", "59"]

        # Mixed separators
        assert parse_cpt_modifiers("25,59;LT") == ["25", "59", "LT"]

        # Single modifier
        assert parse_cpt_modifiers("25") == ["25"]

        # Empty/None
        assert parse_cpt_modifiers("") == []
        assert parse_cpt_modifiers(None) == []

        # Invalid modifiers (too long/short)
        assert parse_cpt_modifiers("1,ABC,59") == ["59"]  # Only 59 is valid

    def test_get_procedure_complexity(self):
        """Test procedure complexity determination"""
        # Simple procedures
        assert get_procedure_complexity("11000") == "low"  # Integumentary
        assert get_procedure_complexity("99211") == "low"  # Simple E&M

        # Moderate procedures
        assert get_procedure_complexity("27000") == "moderate"  # Musculoskeletal
        assert get_procedure_complexity("71020") == "moderate"  # Radiology

        # High complexity procedures
        assert get_procedure_complexity("33000") == "high"  # Cardiovascular
        assert get_procedure_complexity("61000") == "high"  # Neurosurgery

        # Description influence
        assert get_procedure_complexity("99999", "major surgery") == "high"
        assert get_procedure_complexity("99999", "simple procedure") == "low"


class TestCPTCodeIntegration:
    """Test CPT code integration scenarios"""

    def test_display_name_generation(self):
        """Test display name property"""
        cpt = CPTCode(
            uid="test",
            localId="123",
            cptCode="99213",
            name="Office Visit",
            dateTime=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert cpt.display_name == "99213 - Office Visit"

        # No description
        cpt_no_desc = CPTCode(
            uid="test",
            localId="123",
            cptCode="99213",
            name="",
            dateTime=datetime.now(UTC),
            facilityCode="500",
            facilityName="Test",
        )

        assert cpt_no_desc.display_name == "99213"

    def test_field_defaults(self):
        """Test model field defaults"""
        minimal_data = {
            "uid": "test",
            "localId": "123",
            "cptCode": "99213",
            "dateTime": datetime.now(UTC),
            "facilityCode": "500",
            "facilityName": "Test",
        }

        cpt = CPTCode(**minimal_data)

        assert cpt.description == ""  # Default empty string
        assert cpt.quantity == 1  # Default quantity
        assert cpt.status == "completed"  # Default status
        assert cpt.kind == "Procedure"  # Default kind
        assert cpt.modifiers is None  # Default None
        assert cpt.has_modifiers is False


if __name__ == "__main__":
    pytest.main([__file__])
