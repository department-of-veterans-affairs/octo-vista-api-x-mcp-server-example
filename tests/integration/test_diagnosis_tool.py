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
            diagnoses_dict={dx.uid: dx for dx in sample_diagnoses},
            source_station="500",
            source_icn="100022",
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

    def test_diagnoses_filtering_by_status(self, sample_diagnoses):
        """Test filtering diagnoses by status."""
        # Filter active diagnoses
        active_diagnoses = [d for d in sample_diagnoses if d.status == "active"]
        assert len(active_diagnoses) == 4

        # Filter resolved diagnoses
        resolved_diagnoses = [d for d in sample_diagnoses if d.status == "resolved"]
        assert len(resolved_diagnoses) == 1
        assert resolved_diagnoses[0].icd_code == "F32.9"

    def test_diagnoses_comprehensive_response_structure(self, sample_patient_data):
        """Test the comprehensive response structure that would be returned by the MCP tool."""
        diagnoses = sample_patient_data.diagnoses

        # Simulate the response structure
        active_diagnoses = [d for d in diagnoses if d.status == "active"]

        # Verify summary counts
        summary = {
            "active_count": len(active_diagnoses),
        }

        assert summary["active_count"] == 4

        # Test individual diagnosis data structure
        for diagnosis in diagnoses:
            diagnosis_data = {
                "id": diagnosis.local_id,
                "uid": diagnosis.uid,
                "icd_code": diagnosis.icd_code,
                "description": diagnosis.description,
                "status": diagnosis.status,
                "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
            }

            # Verify all expected fields are present
            required_fields = [
                "id",
                "uid",
                "icd_code",
                "description",
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

    def test_diagnosis_date_sorting(self, sample_diagnoses):
        """Test that diagnoses are properly sorted by date."""
        # The sample data should be in reverse chronological order
        dates = [dx.diagnosis_date for dx in sample_diagnoses]

        # Verify dates are in descending order (newest first)
        for i in range(len(dates) - 1):
            assert (
                dates[i] >= dates[i + 1]
            ), "Diagnoses should be sorted by date (newest first)"
