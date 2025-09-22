"""Integration tests for CPT procedures MCP tool"""

from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.models.patient import CPTCode, PatientDataCollection, PatientDemographics
from src.tools.patient.get_patient_procedures import (
    _apply_procedure_filters,
    _build_procedure_summary,
    get_patient_procedures_impl,
)
from src.vista.base import BaseVistaClient


@pytest.fixture
def mock_vista_client():
    """Create mock VistA client"""
    client = Mock(spec=BaseVistaClient)
    client.default_station = "500"
    client.default_duz = "123"
    return client


@pytest.fixture
def sample_cpt_codes():
    """Create sample CPT codes for testing"""
    base_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    codes = [
        CPTCode(
            uid="urn:va:cpt:84F0:237:5326",
            localId="5326",
            cptCode="99213",
            name="Office visit",
            entered=base_date,
            facilityCode="500",
            facilityName="Test Hospital",
            quantity=1,
            encounter="urn:va:visit:500:123:456",
            encounter_name="Primary Care Visit",
        ),
        CPTCode(
            uid="urn:va:cpt:84F0:237:5327",
            localId="5327",
            cptCode="71020",
            name="Chest X-ray",
            entered=base_date,
            facilityCode="500",
            facilityName="Test Hospital",
            quantity=1,
            encounter="urn:va:visit:500:123:789",
            encounter_name="Radiology Visit",
        ),
        CPTCode(
            uid="urn:va:cpt:84F0:237:5328",
            localId="5328",
            cptCode="12001",
            name="Simple repair of superficial wounds",
            entered=base_date,
            facilityCode="500",
            facilityName="Test Hospital",
            quantity=1,
            encounter="urn:va:visit:500:123:456",
            encounter_name="Primary Care Visit",
        ),
    ]

    return codes


@pytest.fixture
def sample_patient_data(sample_cpt_codes):
    """Create sample patient data collection"""
    demographics = PatientDemographics(
        uid="urn:va:patient:500:123",
        dfn="123",
        icn="1234567890",
        fullName="DOE,JOHN",
        familyName="Doe",
        givenNames="John",
        displayName="Doe,John",
        genderCode="M",
        genderName="Male",
        dateOfBirth=datetime(1980, 1, 1, tzinfo=timezone.utc),
        ssn="123456789",
        addresses=[],
        telecoms=[],
        supports=[],
        flags=[],
    )

    return PatientDataCollection(
        demographics=demographics,
        cpt_codes_dict={code.uid: code for code in sample_cpt_codes},
        source_station="500",
        source_icn="1234567890",
    )


class TestCPTProceduresImplementation:
    """Test CPT procedures tool implementation"""

    @pytest.mark.asyncio
    async def test_get_patient_procedures_success(
        self, mock_vista_client, sample_patient_data
    ):
        """Test successful CPT procedures retrieval"""
        # Mock the get_patient_data function
        with patch(
            "src.tools.patient.get_patient_procedures.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            result = await get_patient_procedures_impl(
                vista_client=mock_vista_client,
                patient_icn="1234567890",
                station="500",
                caller_duz="456",
            )

            assert result.success is True
            assert result.metadata.demographics.patient_icn == "1234567890"
            assert len(result.data.procedures) == 3
            assert result.data.total_procedures == 3

            # Check procedure data
            procedures = result.data.procedures
            assert any(p.cpt_code == "99213" for p in procedures)
            assert any(p.cpt_code == "71020" for p in procedures)
            assert any(p.cpt_code == "12001" for p in procedures)

    @pytest.mark.asyncio
    async def test_get_patient_procedures_grouped_by_encounter(
        self, mock_vista_client, sample_patient_data
    ):
        """Test procedures grouped by encounter"""
        with patch(
            "src.tools.patient.get_patient_procedures.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            result = await get_patient_procedures_impl(
                vista_client=mock_vista_client,
                patient_icn="123",
            )

            assert result.success is True
            procedures = result.data.procedures

            # Should have procedures from different encounters
            assert len(procedures) == 3

            # Group procedures by encounter for testing
            encounters = {}
            for proc in procedures:
                encounter_name = proc.encounter_name or "Unknown"
                if encounter_name not in encounters:
                    encounters[encounter_name] = []
                encounters[encounter_name].append(proc)

            # Should have 2 encounters
            assert len(encounters) == 2

            # Check primary care encounter procedures
            primary_care_procs = encounters.get("Primary Care Visit", [])
            assert len(primary_care_procs) == 2
            primary_care_codes = {p.cpt_code for p in primary_care_procs}
            assert "99213" in primary_care_codes
            assert "12001" in primary_care_codes

            # Check radiology encounter procedures
            radiology_procs = encounters.get("Radiology Visit", [])
            assert len(radiology_procs) == 1
            assert radiology_procs[0].cpt_code == "71020"


class TestCPTFilteringFunctions:
    """Test CPT filtering helper functions"""

    def test_apply_procedure_filters_date_range(self, sample_cpt_codes):
        """Test filtering by date range"""
        filtered = _apply_procedure_filters(
            sample_cpt_codes,
            date_from=date(2024, 1, 1),
            date_to=date(2024, 1, 31),
        )

        # All sample codes are from 2024-01-01, so all should be included
        assert len(filtered) == 3

        # Test excluding date range
        filtered = _apply_procedure_filters(
            sample_cpt_codes, date_from=date(2024, 2, 1)
        )

        assert len(filtered) == 0

    def test_build_procedure_summary(self, sample_cpt_codes):
        """Test building procedure summary statistics"""
        summary = _build_procedure_summary(sample_cpt_codes, sample_cpt_codes)

        required_fields = [
            "total_procedures",
            "filtered_procedures",
            "unique_encounters",
        ]

        for field in required_fields:
            assert field in summary

        assert summary["total_procedures"] == 3
        assert summary["filtered_procedures"] == 3
        assert summary["unique_encounters"] == 2  # 2 different encounters


class TestCPTErrorHandling:
    """Test error handling in CPT procedures tool"""

    @pytest.mark.asyncio
    async def test_invalid_patient_dfn(self, mock_vista_client):
        """Test handling of invalid patient DFN"""
        with patch(
            "src.tools.patient.get_patient_procedures.get_patient_data"
        ) as mock_get_data:
            mock_get_data.side_effect = Exception("Patient not found")

            result = await get_patient_procedures_impl(
                vista_client=mock_vista_client,
                patient_icn="invalid",
            )

            assert result.success is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_no_procedures_found(self, mock_vista_client):
        """Test handling when no procedures are found"""
        # Create patient data with no CPT codes
        demographics = PatientDemographics(
            uid="urn:va:patient:500:123",
            dfn="123",
            icn="1234567890",
            fullName="DOE,JOHN",
            familyName="Doe",
            givenNames="John",
            displayName="Doe,John",
            genderCode="M",
            genderName="Male",
            dateOfBirth=datetime(1980, 1, 1, tzinfo=timezone.utc),
            ssn="123456789",
            addresses=[],
            telecoms=[],
            supports=[],
            flags=[],
        )

        empty_patient_data = PatientDataCollection(
            demographics=demographics,
            cpt_codes_dict={},  # No CPT codes
            source_station="500",
            source_icn="123",
        )

        with patch(
            "src.tools.patient.get_patient_procedures.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = empty_patient_data

            result = await get_patient_procedures_impl(
                vista_client=mock_vista_client,
                patient_icn="123",
            )

            assert result.success is True
            assert len(result.data.procedures) == 0
            assert result.data.total_procedures == 0


if __name__ == "__main__":
    pytest.main([__file__])
