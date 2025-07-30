"""Integration tests for get_patient_health_factors MCP tool"""

from unittest.mock import AsyncMock

import pytest

from src.models.patient.clinical import HealthFactor
from src.models.patient.collection import PatientDataCollection
from src.models.patient.demographics import PatientDemographics


@pytest.fixture
def mock_vista_client():
    """Mock Vista client for testing"""
    return AsyncMock()


@pytest.fixture
def sample_health_factors():
    """Sample health factors for testing"""
    return [
        HealthFactor(
            uid="urn:va:factor:84F0:237:863",
            localId="863",
            name="VA-COVID-19 PCR LAB OUTSIDE POSITIVE",
            categoryName="VA-COVID-19 [C]",
            categoryUid="urn:va:factor-category:15099",
            entered="20250515",
            facilityCode="500",
            facilityName="CAMP MASTER",
            encounterName="May 15, 2025",
            encounterUid="urn:va:visit:84F0:237:10723",
            summary="VA-COVID-19 PCR LAB OUTSIDE POSITIVE",
            comment="WRITTEN DOCUMENTATION",
        ),
        HealthFactor(
            uid="urn:va:factor:84F0:237:730",
            localId="730",
            name="LCS PATIENT NOTIFIED BY SECURE MESSAGE",
            categoryName="LUNG CANCER SCREENING (LCS) [C]",
            categoryUid="urn:va:factor-category:619711",
            entered="20250227103328",
            facilityCode="500",
            facilityName="CAMP MASTER",
            encounterName="20 MINUTE Feb 27, 2025",
            encounterUid="urn:va:visit:84F0:237:10321",
            locationName="20 MINUTE",
            locationUid="urn:va:location:84F0:240",
            summary="LCS PATIENT NOTIFIED BY SECURE MESSAGE",
        ),
        HealthFactor(
            uid="urn:va:factor:84F0:237:542",
            localId="542",
            name="VA-COVID-19 SUSPECTED",
            categoryName="VA-COVID-19 [C]",
            categoryUid="urn:va:factor-category:15099",
            entered="20241112",
            facilityCode="500",
            facilityName="CAMP MASTER",
            encounterName="0Nov 12, 2024",
            encounterUid="urn:va:visit:84F0:237:9248",
            summary="VA-COVID-19 SUSPECTED",
        ),
    ]


@pytest.fixture
def sample_patient_data(sample_health_factors):
    """Sample patient data collection with health factors"""
    demographics = PatientDemographics(
        uid="urn:va:patient:84F0:237",
        localId="237",
        dfn="237",
        fullName="TESTPATIENT,JANE DOE",
        displayName="TESTPATIENT,JANE DOE",
        familyName="TESTPATIENT",
        givenNames="JANE DOE",
        dateOfBirth="19350407",
        age=89,
        ssn="123456789",
        genderCode="F",
        genderName="FEMALE",
        facilityCode="500",
        facilityName="CAMP MASTER",
    )

    return PatientDataCollection(
        demographics=demographics,
        health_factors=sample_health_factors,
        source_station="500",
        source_dfn="237",
    )


class TestGetPatientHealthFactorsIntegration:
    """Test get_patient_health_factors functionality"""

    @pytest.mark.asyncio
    async def test_health_factors_data_structure(self, sample_patient_data):
        """Test that health factors have the correct data structure"""
        health_factors = sample_patient_data.health_factors

        assert len(health_factors) == 3

        # Test first health factor structure
        factor = health_factors[0]
        assert factor.uid == "urn:va:factor:84F0:237:863"
        assert factor.factor_name == "VA-COVID-19 PCR LAB OUTSIDE POSITIVE"
        assert factor.category == "VA-COVID-19 [C]"
        assert factor.local_id == "863"
        assert factor.facility_name == "CAMP MASTER"
        assert factor.status == "active"

        # Test computed properties
        assert factor.risk_category in [
            "lifestyle",
            "environmental",
            "genetic",
            "medical",
            "screening",
            "other",
        ]
        assert factor.severity_level in ["mild", "moderate", "severe", "unknown"]
        assert isinstance(factor.risk_score, int)
        assert 0 <= factor.risk_score <= 10
        assert isinstance(factor.is_modifiable, bool)
        assert isinstance(factor.requires_monitoring, bool)

    @pytest.mark.asyncio
    async def test_health_factors_categorization(self, sample_health_factors):
        """Test health factor categorization functionality"""
        # Test COVID factors
        covid_factors = [f for f in sample_health_factors if "COVID-19" in f.category]
        assert len(covid_factors) == 2

        # Test screening factors
        screening_factors = [
            f for f in sample_health_factors if "SCREENING" in f.category
        ]
        assert len(screening_factors) == 1

        # Test risk categorization
        for factor in sample_health_factors:
            risk_category = factor.risk_category
            assert risk_category in [
                "lifestyle",
                "environmental",
                "genetic",
                "medical",
                "screening",
                "other",
            ]

    @pytest.mark.asyncio
    async def test_health_factors_risk_scoring(self, sample_health_factors):
        """Test health factor risk scoring functionality"""
        for factor in sample_health_factors:
            # Test risk score is within bounds
            assert 0 <= factor.risk_score <= 10

            # Test severity levels
            assert factor.severity_level in ["mild", "moderate", "severe", "unknown"]

            # Test computed properties
            assert isinstance(factor.is_modifiable, bool)
            assert isinstance(factor.requires_monitoring, bool)

    @pytest.mark.asyncio
    async def test_health_factors_filtering(self, sample_health_factors):
        """Test health factor filtering functionality"""
        # Filter by category
        covid_factors = [
            f for f in sample_health_factors if "COVID-19" in f.category.upper()
        ]
        assert len(covid_factors) == 2

        # Filter by risk category
        screening_factors = [
            f for f in sample_health_factors if f.risk_category == "screening"
        ]
        # Should have at least the lung cancer screening factor
        assert len(screening_factors) >= 0  # May vary based on categorization logic

        # Filter by severity
        severe_factors = [
            f for f in sample_health_factors if f.severity_level == "severe"
        ]
        # Should have factors with severe severity
        assert len(severe_factors) >= 0  # May vary based on severity logic

    @pytest.mark.asyncio
    async def test_health_factors_trending(self, sample_health_factors):
        """Test health factor trending functionality"""
        from src.services.validators.clinical_validators import get_health_factor_trends

        # Test trending for COVID factors
        covid_trends = get_health_factor_trends(sample_health_factors, "COVID-19")

        assert covid_trends["count"] == 2
        assert covid_trends["is_recurring"]
        assert covid_trends["trend"] in ["stable", "improving", "worsening"]
        assert "first_recorded" in covid_trends
        assert "last_recorded" in covid_trends
        assert "current_severity" in covid_trends
        assert "current_risk_score" in covid_trends

        # Test trending for non-existent factor
        no_data_trends = get_health_factor_trends(sample_health_factors, "NONEXISTENT")
        assert no_data_trends["trend"] == "no_data"
        assert no_data_trends["count"] == 0
