"""Unit tests for health factor parsing and categorization"""

from datetime import datetime

from src.models.patient.health_factor import HealthFactor
from src.services.parsers.patient.patient_parser import PatientDataParser
from src.services.validators.clinical_validators import (
    calculate_health_factor_risk_score,
    categorize_health_factor,
    get_health_factor_trends,
    normalize_health_factor_severity,
)


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

    def test_health_factor_properties(self):
        """Test computed properties of health factor"""
        factor_data = {
            "uid": "urn:va:factor:84F0:237:730",
            "localId": "730",
            "name": "LCS PATIENT NOTIFIED BY SECURE MESSAGE",
            "categoryName": "LUNG CANCER SCREENING (LCS) [C]",
            "entered": "20250227",
            "facilityCode": "500",
            "facilityName": "CAMP MASTER",
        }

        factor = HealthFactor(**factor_data)

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


class TestHealthFactorCategorization:
    """Test health factor categorization utilities"""

    def test_lifestyle_categorization(self):
        """Test lifestyle factor categorization"""
        # Smoking-related
        category = categorize_health_factor(
            "TOBACCO USE [C]", "TOBACCO SMOKING CURRENT"
        )
        assert category == "lifestyle"

        # Alcohol-related
        category = categorize_health_factor("SUBSTANCE [C]", "ALCOHOL DEPENDENCY")
        assert category == "lifestyle"

        # Exercise-related
        category = categorize_health_factor("ACTIVITY [C]", "SEDENTARY LIFESTYLE")
        assert category == "lifestyle"

    def test_environmental_categorization(self):
        """Test environmental factor categorization"""
        # Agent Orange
        category = categorize_health_factor("EXPOSURE [C]", "AGENT ORANGE EXPOSURE")
        assert category == "environmental"

        # Radiation
        category = categorize_health_factor(
            "MILITARY [C]", "IONIZING RADIATION EXPOSURE"
        )
        assert category == "environmental"

        # Combat exposure
        category = categorize_health_factor("MILITARY [C]", "COMBAT VETERAN")
        assert category == "environmental"

    def test_screening_categorization(self):
        """Test screening factor categorization"""
        # Cancer screening
        category = categorize_health_factor(
            "LUNG CANCER SCREENING (LCS) [C]", "LCS INITIAL IMAGE DATE"
        )
        assert category == "screening"

        # Preventive care
        category = categorize_health_factor("PREVENTION [C]", "MAMMOGRAM SCREENING")
        assert category == "screening"

    def test_medical_categorization(self):
        """Test medical condition categorization"""
        # Diabetes
        category = categorize_health_factor("CHRONIC DISEASE [C]", "DIABETES TYPE 2")
        assert category == "medical"

        # Hypertension
        category = categorize_health_factor("CARDIOVASCULAR [C]", "HYPERTENSION")
        assert category == "medical"

    def test_unknown_categorization(self):
        """Test unknown/other categorization"""
        category = categorize_health_factor("", "")
        assert category == "unknown"

        category = categorize_health_factor("RANDOM [C]", "SOME RANDOM FACTOR")
        assert category == "other"


class TestHealthFactorSeverity:
    """Test severity normalization"""

    def test_explicit_severity(self):
        """Test explicit severity values"""
        severity = normalize_health_factor_severity("", "", "mild")
        assert severity == "mild"

        severity = normalize_health_factor_severity("", "", "SEVERE")
        assert severity == "severe"

        severity = normalize_health_factor_severity("", "", "moderate")
        assert severity == "moderate"

    def test_inferred_severity(self):
        """Test severity inferred from factor name"""
        # High severity
        severity = normalize_health_factor_severity(
            "COVID-19 [C]", "COVID-19 POSITIVE", None
        )
        assert severity == "severe"

        # Moderate severity
        severity = normalize_health_factor_severity(
            "COVID-19 [C]", "COVID-19 SUSPECTED", None
        )
        assert severity == "moderate"

        # Low severity
        severity = normalize_health_factor_severity(
            "SCREENING [C]", "MAMMOGRAM SCREENING", None
        )
        assert severity == "mild"

    def test_unknown_severity(self):
        """Test unknown severity"""
        severity = normalize_health_factor_severity(
            "GENERAL [C]", "GENERAL FACTOR", None
        )
        assert severity == "unknown"


class TestHealthFactorRiskScore:
    """Test risk score calculation"""

    def test_high_risk_score(self):
        """Test high-risk conditions"""
        score = calculate_health_factor_risk_score(
            "CANCER [C]", "LUNG CANCER POSITIVE", "severe"
        )
        assert score >= 8

        score = calculate_health_factor_risk_score(
            "CARDIAC [C]", "CARDIAC EMERGENCY", "severe"
        )
        assert score >= 8

    def test_moderate_risk_score(self):
        """Test moderate-risk conditions"""
        score = calculate_health_factor_risk_score(
            "SCREENING [C]", "ELEVATED BLOOD PRESSURE", "moderate"
        )
        assert 4 <= score <= 7

        score = calculate_health_factor_risk_score(
            "COVID-19 [C]", "COVID-19 SUSPECTED", "moderate"
        )
        assert 4 <= score <= 7

    def test_low_risk_score(self):
        """Test low-risk conditions"""
        score = calculate_health_factor_risk_score(
            "PREVENTION [C]", "ROUTINE SCREENING", "mild"
        )
        assert score <= 4

        score = calculate_health_factor_risk_score(
            "EDUCATION [C]", "HEALTH EDUCATION", "mild"
        )
        assert score <= 4

    def test_score_bounds(self):
        """Test risk score is within bounds"""
        # Test various combinations
        test_cases = [
            ("SEVERE [C]", "CRITICAL CONDITION", "severe"),
            ("MILD [C]", "MINOR ISSUE", "mild"),
            ("UNKNOWN [C]", "RANDOM FACTOR", "unknown"),
        ]

        for category, factor, severity in test_cases:
            score = calculate_health_factor_risk_score(category, factor, severity)
            assert (
                0 <= score <= 10
            ), f"Score {score} out of bounds for {category}, {factor}, {severity}"


class TestHealthFactorTrends:
    """Test health factor trending analysis"""

    def test_no_data_trend(self):
        """Test trend analysis with no matching factors"""
        health_factors = []
        trends = get_health_factor_trends(health_factors, "NONEXISTENT FACTOR")

        assert trends["trend"] == "no_data"
        assert trends["count"] == 0

    def test_single_factor_trend(self):
        """Test trend with single factor"""
        # Create mock health factor
        factor_data = {
            "uid": "urn:va:factor:84F0:237:863",
            "localId": "863",
            "name": "COVID-19 POSITIVE",
            "categoryName": "COVID-19 [C]",
            "entered": "20250515",
            "facilityCode": "500",
            "facilityName": "CAMP MASTER",
        }

        factor = HealthFactor(**factor_data)
        trends = get_health_factor_trends([factor], "COVID-19")

        assert trends["trend"] == "stable"
        assert trends["count"] == 1
        assert not trends["is_recurring"]
        assert "first_recorded" in trends
        assert "current_severity" in trends

    def test_multiple_factor_trend(self):
        """Test trend with multiple factors"""
        # Create multiple mock factors with different dates and severities
        factors = []
        for i, date in enumerate(["20250101", "20250201", "20250301"]):
            factor_data = {
                "uid": f"urn:va:factor:84F0:237:{i}",
                "localId": str(i),
                "name": f"BLOOD PRESSURE ELEVATED {i}",
                "categoryName": "CARDIOVASCULAR [C]",
                "entered": date,
                "facilityCode": "500",
                "facilityName": "CAMP MASTER",
            }
            factors.append(HealthFactor(**factor_data))

        trends = get_health_factor_trends(factors, "BLOOD PRESSURE")

        assert trends["count"] == 3
        assert trends["is_recurring"]
        assert trends["trend"] in ["stable", "improving", "worsening"]
        assert len(trends["severity_progression"]) == 3


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

        assert len(health_factors) == 1
        factor = health_factors[0]
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

        assert len(health_factors) == 1
        factor = health_factors[0]
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
        assert len(health_factors) == 1
        assert health_factors[0].factor_name == "VALID FACTOR"
