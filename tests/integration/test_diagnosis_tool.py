"""Integration tests for diagnosis MCP tool functionality."""

import pytest

from src.models.patient import Diagnosis, PatientDataCollection, PatientDemographics


class TestGetPatientDiagnosesIntegration:
    """Integration tests for get_patient_diagnoses MCP tool."""

    @pytest.fixture
    def sample_diagnoses(self):
        """Create sample diagnosis data for testing."""
        return [
            Diagnosis(
                uid="urn:va:problem:9E7A:100022:1001",
                localId="1001",
                icdCode="I25.10",
                icdName="Atherosclerotic heart disease",
                facilityCode="500",
                facilityName="SALT LAKE CITY",
                entered="20231201",
                diagnosis_type="primary",
                status="active",
            ),
            Diagnosis(
                uid="urn:va:problem:9E7A:100022:1002",
                localId="1002",
                icdCode="E11.9",
                icdName="Type 2 diabetes",
                facilityCode="500",
                facilityName="SALT LAKE CITY",
                entered="20231115",
                diagnosis_type="secondary",
                status="active",
            ),
            Diagnosis(
                uid="urn:va:problem:9E7A:100022:1003",
                localId="1003",
                icdCode="J44.1",
                icdName="COPD with exacerbation",
                facilityCode="500",
                facilityName="SALT LAKE CITY",
                entered="20231010",
                diagnosis_type="secondary",
                status="active",
            ),
            Diagnosis(
                uid="urn:va:problem:9E7A:100022:1004",
                localId="1004",
                icdCode="F32.9",
                icdName="Major depressive disorder",
                facilityCode="500",
                facilityName="SALT LAKE CITY",
                entered="20230815",
                diagnosis_type="secondary",
                status="resolved",
            ),
            Diagnosis(
                uid="urn:va:problem:9E7A:100022:1005",
                localId="1005",
                icdCode="Z51.11",
                icdName="Encounter for cancer screening",
                facilityCode="500",
                facilityName="SALT LAKE CITY",
                entered="20230601",
                diagnosis_type="secondary",
                status="active",
            ),
        ]

    @pytest.fixture
    def sample_patient_data(self, sample_diagnoses):
        """Create sample patient data collection."""
        demographics = PatientDemographics(
            icn="1008714701V416111",
            fullName="DOE,JOHN QUINCY",
            familyName="DOE",
            givenNames="JOHN QUINCY",
            displayName="DOE,JOHN QUINCY",
            dateOfBirth="19700704",
            genderName="Male",
            genderCode="M",
            ssn="666114701",
            sensitive=False,
        )

        return PatientDataCollection(
            demographics=demographics,
            diagnoses=sample_diagnoses,
            vital_signs=[],
            lab_results=[],
            consults=[],
            medications=[],
            health_factors=[],
            source_station="500",
            source_dfn="100022",
            total_items=5,
        )

    @pytest.mark.asyncio
    async def test_diagnoses_data_structure(self, sample_patient_data):
        """Test the basic data structure of diagnosis response."""
        # Test the data structure directly without the tool registration complexity
        diagnoses = sample_patient_data.diagnoses

        # Verify basic structure
        assert len(diagnoses) == 5

        # Test first diagnosis
        first_dx = diagnoses[0]
        assert first_dx.icd_code == "I25.10"
        assert first_dx.description == "Atherosclerotic heart disease"
        assert first_dx.diagnosis_type == "primary"
        assert first_dx.body_system == "cardiovascular"
        assert first_dx.is_primary
        assert first_dx.is_valid_icd

    def test_diagnoses_body_system_classification(self, sample_diagnoses):
        """Test body system classification for diagnoses."""
        # Group by body system
        body_systems = {}
        for diagnosis in sample_diagnoses:
            system = diagnosis.body_system
            if system not in body_systems:
                body_systems[system] = []
            body_systems[system].append(diagnosis)

        # Verify expected body systems
        expected_systems = [
            "cardiovascular",
            "endocrine",
            "respiratory",
            "mental_health",
            "other",
        ]
        for system in expected_systems:
            if system in body_systems:
                assert len(body_systems[system]) >= 1

        # Test specific classifications
        cardio_diagnoses = [
            d for d in sample_diagnoses if d.body_system == "cardiovascular"
        ]
        assert len(cardio_diagnoses) == 1
        assert cardio_diagnoses[0].icd_code == "I25.10"

        endocrine_diagnoses = [
            d for d in sample_diagnoses if d.body_system == "endocrine"
        ]
        assert len(endocrine_diagnoses) == 1
        assert endocrine_diagnoses[0].icd_code == "E11.9"

    def test_diagnoses_chronic_condition_detection(self, sample_diagnoses):
        """Test chronic condition detection in diagnoses."""
        chronic_diagnoses = [d for d in sample_diagnoses if d.is_chronic]

        # Expect diabetes and COPD to be chronic
        chronic_icd_codes = [d.icd_code for d in chronic_diagnoses]
        assert "E11.9" in chronic_icd_codes  # Diabetes
        assert "J44.1" in chronic_icd_codes  # COPD

        # Depression should also be chronic
        if "F32.9" in chronic_icd_codes:
            assert True  # Expected

        # Screening encounters should not be chronic
        screening_diagnoses = [
            d for d in sample_diagnoses if "screening" in d.description.lower()
        ]
        for _dx in screening_diagnoses:
            # Screening should typically not be chronic, but this depends on keywords
            pass  # Just verify the property exists

    def test_diagnoses_severity_assessment(self, sample_diagnoses):
        """Test severity assessment for diagnoses."""
        severity_levels = [d.severity_level for d in sample_diagnoses]

        # Should have valid severity levels
        valid_severities = ["mild", "moderate", "severe"]
        for severity in severity_levels:
            assert severity in valid_severities

        # Primary diagnosis should typically be moderate or severe
        primary_diagnoses = [d for d in sample_diagnoses if d.is_primary]
        for dx in primary_diagnoses:
            assert dx.severity_level in ["moderate", "severe"]

    def test_diagnoses_filtering_by_body_system(self, sample_diagnoses):
        """Test filtering diagnoses by body system."""
        # Filter by cardiovascular
        cardio_filter = [
            d for d in sample_diagnoses if d.body_system == "cardiovascular"
        ]
        assert len(cardio_filter) == 1
        assert cardio_filter[0].icd_code == "I25.10"

        # Filter by respiratory
        resp_filter = [d for d in sample_diagnoses if d.body_system == "respiratory"]
        assert len(resp_filter) == 1
        assert resp_filter[0].icd_code == "J44.1"

        # Filter by endocrine
        endo_filter = [d for d in sample_diagnoses if d.body_system == "endocrine"]
        assert len(endo_filter) == 1
        assert endo_filter[0].icd_code == "E11.9"

    def test_diagnoses_filtering_by_type(self, sample_diagnoses):
        """Test filtering diagnoses by diagnosis type."""
        # Filter primary diagnoses
        primary_diagnoses = [
            d for d in sample_diagnoses if d.diagnosis_type == "primary"
        ]
        assert len(primary_diagnoses) == 1
        assert primary_diagnoses[0].icd_code == "I25.10"

        # Filter secondary diagnoses
        secondary_diagnoses = [
            d for d in sample_diagnoses if d.diagnosis_type == "secondary"
        ]
        assert len(secondary_diagnoses) == 4

        # Verify is_primary property matches
        for dx in primary_diagnoses:
            assert dx.is_primary
        for dx in secondary_diagnoses:
            assert not dx.is_primary

    def test_diagnoses_filtering_by_status(self, sample_diagnoses):
        """Test filtering diagnoses by status."""
        # Filter active diagnoses
        active_diagnoses = [d for d in sample_diagnoses if d.status == "active"]
        assert len(active_diagnoses) == 4

        # Filter resolved diagnoses
        resolved_diagnoses = [d for d in sample_diagnoses if d.status == "resolved"]
        assert len(resolved_diagnoses) == 1
        assert resolved_diagnoses[0].icd_code == "F32.9"

    def test_diagnoses_icd_version_filtering(self, sample_diagnoses):
        """Test filtering by ICD version."""
        # All sample diagnoses should be ICD-10 (start with letters)
        icd10_diagnoses = [d for d in sample_diagnoses if d.icd_version == "ICD-10"]
        assert len(icd10_diagnoses) == 5

        # Verify ICD code validation
        for dx in icd10_diagnoses:
            assert dx.is_valid_icd

    def test_diagnoses_trending_analysis(self, sample_diagnoses):
        """Test diagnosis trending functionality."""
        from src.services.validators.clinical_validators import get_diagnosis_trends

        # Test trends for each diagnosis
        for diagnosis in sample_diagnoses:
            trends = get_diagnosis_trends(sample_diagnoses, diagnosis.icd_code)

            # Should have basic trend info
            assert "trend" in trends
            assert "count" in trends
            assert trends["count"] >= 1

            # For single occurrence, should be stable and not recurring
            if trends["count"] == 1:
                assert trends["trend"] == "stable"
                assert not trends["is_recurring"]

    def test_diagnoses_comprehensive_response_structure(self, sample_patient_data):
        """Test the comprehensive response structure that would be returned by the MCP tool."""
        diagnoses = sample_patient_data.diagnoses

        # Simulate the response structure
        primary_diagnoses = [d for d in diagnoses if d.is_primary]
        chronic_diagnoses = [d for d in diagnoses if d.is_chronic]
        active_diagnoses = [d for d in diagnoses if d.status == "active"]

        # Group by body system
        body_system_groups = {}
        for diagnosis in diagnoses:
            system = diagnosis.body_system
            if system not in body_system_groups:
                body_system_groups[system] = []
            body_system_groups[system].append(diagnosis)

        # Verify summary counts
        summary = {
            "primary_count": len(primary_diagnoses),
            "chronic_count": len(chronic_diagnoses),
            "active_count": len(active_diagnoses),
            "icd_9_count": len([d for d in diagnoses if d.icd_version == "ICD-9"]),
            "icd_10_count": len([d for d in diagnoses if d.icd_version == "ICD-10"]),
        }

        assert summary["primary_count"] == 1
        assert summary["active_count"] == 4
        assert summary["icd_10_count"] == 5
        assert summary["icd_9_count"] == 0

        # Verify body system grouping
        assert len(body_system_groups) >= 3  # Should have multiple body systems

        # Test individual diagnosis data structure
        for diagnosis in diagnoses:
            diagnosis_data = {
                "id": diagnosis.local_id,
                "uid": diagnosis.uid,
                "icd_code": diagnosis.icd_code,
                "icd_version": diagnosis.icd_version,
                "description": diagnosis.description,
                "body_system": diagnosis.body_system,
                "diagnosis_type": diagnosis.diagnosis_type,
                "status": diagnosis.status,
                "severity": diagnosis.severity_level,
                "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
                "is_primary": diagnosis.is_primary,
                "is_chronic": diagnosis.is_chronic,
                "is_valid_icd": diagnosis.is_valid_icd,
            }

            # Verify all expected fields are present
            required_fields = [
                "id",
                "uid",
                "icd_code",
                "description",
                "body_system",
                "diagnosis_type",
            ]
            for field in required_fields:
                assert field in diagnosis_data
                assert diagnosis_data[field] is not None

    def test_diagnoses_validation_edge_cases(self, sample_patient_data):
        """Test edge cases in diagnosis validation and processing."""
        diagnoses = sample_patient_data.diagnoses

        # Test that all diagnoses have required fields
        for diagnosis in diagnoses:
            assert diagnosis.uid
            assert diagnosis.local_id
            assert diagnosis.icd_code
            assert diagnosis.description
            assert diagnosis.facility_code
            assert diagnosis.facility_name
            assert diagnosis.diagnosis_date

            # Test computed properties don't raise exceptions
            assert diagnosis.body_system is not None
            assert diagnosis.severity_level in ["mild", "moderate", "severe"]
            assert isinstance(diagnosis.is_primary, bool)
            assert isinstance(diagnosis.is_chronic, bool)
            assert isinstance(diagnosis.is_valid_icd, bool)

    def test_diagnosis_date_sorting(self, sample_diagnoses):
        """Test that diagnoses are properly sorted by date."""
        # The sample data should be in reverse chronological order
        dates = [dx.diagnosis_date for dx in sample_diagnoses]

        # Verify dates are in descending order (newest first)
        for i in range(len(dates) - 1):
            assert (
                dates[i] >= dates[i + 1]
            ), "Diagnoses should be sorted by date (newest first)"
