"""Unit tests for health factor parsing and categorization"""

from datetime import datetime

from src.models.patient.health_factor import HealthFactor
from src.services.parsers.patient.patient_parser import PatientDataParser


class TestHealthFactorModel:
    """Test HealthFactor Pydantic model"""

    def test_create_health_factor_basic(self):
        """Test creating a basic health factor"""
        factor_data = {
            "uid": "urn:va:factor:84F0:237:863",
            "localId": "863",
            "name": "VA-COVID-19 PCR LAB OUTSIDE POSITIVE",
            "categoryName": "VA-COVID-19 [C]",
            "categoryUid": "urn:va:factor-category:15099",
            "entered": "20250515",
            "facilityCode": "500",
            "facilityName": "CAMP MASTER",
            "encounterName": "May 15, 2025",
            "encounterUid": "urn:va:visit:84F0:237:10723",
            "summary": "VA-COVID-19 PCR LAB OUTSIDE POSITIVE",
            "display": True,
            "kind": "Health Factor",
        }

        factor = HealthFactor(**factor_data)

        assert factor.uid == "urn:va:factor:84F0:237:863"
        assert factor.factor_name == "VA-COVID-19 PCR LAB OUTSIDE POSITIVE"
        assert factor.category == "VA-COVID-19 [C]"
        assert factor.local_id == "863"
        assert factor.facility_name == "CAMP MASTER"
        assert factor.status == "active"  # default
        assert isinstance(factor.recorded_date, datetime)


class TestHealthFactorParser:
    """Test health factor parsing in PatientDataParser"""

    def test_parse_health_factors_basic(self):
        """Test basic health factor parsing"""
        parser = PatientDataParser("500", "237")

        factor_items = [
            {
                "uid": "urn:va:factor:84F0:237:863",
                "localId": 863,
                "name": "VA-COVID-19 PCR LAB OUTSIDE POSITIVE",
                "categoryName": "VA-COVID-19 [C]",
                "entered": 20250515,
                "facilityCode": 500,
                "facilityName": "CAMP MASTER",
                "kind": "Health Factor",
            }
        ]

        health_factors = parser._parse_health_factors(factor_items)

        # Now returns dict keyed by UID
        assert isinstance(health_factors, dict)
        assert len(health_factors) == 1
        assert "urn:va:factor:84F0:237:863" in health_factors
        factor = health_factors["urn:va:factor:84F0:237:863"]
        assert factor.factor_name == "VA-COVID-19 PCR LAB OUTSIDE POSITIVE"
        assert factor.category == "VA-COVID-19 [C]"
        assert factor.local_id == "863"
        assert factor.facility_name == "CAMP MASTER"

    def test_parse_health_factors_with_preprocessing(self):
        """Test health factor parsing with missing fields"""
        parser = PatientDataParser("500", "237")

        factor_items = [
            {
                "uid": "urn:va:factor:84F0:237:999",
                # Missing name, categoryName, facilityCode, facilityName, entered, localId
            }
        ]

        health_factors = parser._parse_health_factors(factor_items)

        assert isinstance(health_factors, dict)
        assert len(health_factors) == 1
        assert "urn:va:factor:84F0:237:999" in health_factors
        factor = health_factors["urn:va:factor:84F0:237:999"]
        assert factor.factor_name == "UNKNOWN HEALTH FACTOR"
        assert factor.category == "GENERAL"
        assert factor.facility_name == "UNKNOWN FACILITY"
        assert factor.local_id == "999"  # Extracted from UID

    def test_parse_health_factors_error_handling(self):
        """Test error handling in health factor parsing"""
        parser = PatientDataParser("500", "237")

        # Invalid data that will cause parsing errors
        factor_items = [
            {"invalid": "data"},  # Missing required fields
            {
                "uid": "urn:va:factor:84F0:237:863",
                "localId": 863,
                "name": "VALID FACTOR",
                "categoryName": "VALID [C]",
                "entered": 20250515,
                "facilityCode": 500,
                "facilityName": "CAMP MASTER",
            },
        ]

        # Should parse the valid one and skip the invalid one
        health_factors = parser._parse_health_factors(factor_items)
        assert isinstance(health_factors, dict)
        assert len(health_factors) == 1
        assert "urn:va:factor:84F0:237:863" in health_factors
        assert (
            health_factors["urn:va:factor:84F0:237:863"].factor_name == "VALID FACTOR"
        )
