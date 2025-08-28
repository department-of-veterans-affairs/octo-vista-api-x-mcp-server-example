"""Unit tests for CPT code parsing and validation"""

from datetime import UTC, datetime

import pytest

from src.models.patient.cpt_code import CPTCode
from src.services.validators.cpt_validators import (
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
            "entered": "20240101120000",
            "facilityCode": "500",
            "facilityName": "Test Hospital",
        }

        cpt = CPTCode(**data)

        assert cpt.uid == "urn:va:cpt:84F0:237:5326"
        assert cpt.local_id == "5326"
        assert cpt.cpt_code == "82950"  # Should strip URN prefix
        assert cpt.name == "Glucose"
        assert isinstance(cpt.entered, datetime)
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

        assert cpt.name == ""  # Default empty string
        assert cpt.quantity == 1  # Default quantity


if __name__ == "__main__":
    pytest.main([__file__])
