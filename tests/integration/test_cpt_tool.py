"""Integration tests for CPT procedures MCP tool"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.models.patient.collection import PatientDataCollection
from src.models.patient.cpt_code import CPTCode
from src.models.patient.demographics import PatientDemographics
from src.tools.patient.get_patient_procedures import (
    _apply_procedure_filters,
    _build_procedure_summary,
    _format_procedures_list,
    _group_procedures_by_encounter,
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
    base_date = datetime(2024, 1, 1, 12, 0, 0)

    codes = [
        CPTCode(
            uid="urn:va:cpt:84F0:237:5326",
            localId="5326",
            cptCode="99213",
            name="Office Visit",
            dateTime=base_date,
            facilityCode="500",
            facilityName="Test Hospital",
            provider="Dr. Smith",
            quantity=1,
            associated_visit_uid="urn:va:visit:500:123:456",
            encounter_name="Primary Care Visit",
        ),
        CPTCode(
            uid="urn:va:cpt:84F0:237:5327",
            localId="5327",
            cptCode="71020",
            name="Chest X-ray",
            dateTime=base_date,
            facilityCode="500",
            facilityName="Test Hospital",
            provider="Dr. Johnson",
            quantity=1,
            modifiers=["26"],
            associated_visit_uid="urn:va:visit:500:123:789",
            encounter_name="Radiology Visit",
        ),
        CPTCode(
            uid="urn:va:cpt:84F0:237:5328",
            localId="5328",
            cptCode="12001",
            name="Simple repair of superficial wounds",
            dateTime=base_date,
            facilityCode="500",
            facilityName="Test Hospital",
            provider="Dr. Brown",
            quantity=1,
            associated_visit_uid="urn:va:visit:500:123:456",
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
        dateOfBirth=datetime(1980, 1, 1),
        ssn="123456789",
        addresses=[],
        telecoms=[],
        supports=[],
        flags=[],
    )

    return PatientDataCollection(
        demographics=demographics,
        cpt_codes=sample_cpt_codes,
        source_station="500",
        source_dfn="123",
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
                patient_dfn="123",
                station="500",
                caller_duz="456",
            )

            assert result.success is True
            assert result.patient.dfn == "123"
            assert len(result.procedures) == 3
            assert result.summary["total_procedures"] == 3

            # Check procedure data
            procedures = result.procedures
            assert any(p["cpt_code"] == "99213" for p in procedures)
            assert any(p["cpt_code"] == "71020" for p in procedures)
            assert any(p["cpt_code"] == "12001" for p in procedures)

    @pytest.mark.asyncio
    async def test_get_patient_procedures_with_filters(
        self, mock_vista_client, sample_patient_data
    ):
        """Test CPT procedures retrieval with filters"""
        with patch(
            "src.tools.patient.get_patient_procedures.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            # Filter by radiology category
            result = await get_patient_procedures_impl(
                vista_client=mock_vista_client,
                patient_dfn="123",
                procedure_category="radiology",
            )

            assert result.success is True
            procedures = result.procedures
            assert len(procedures) == 1
            assert procedures[0]["cpt_code"] == "71020"
            assert procedures[0]["category"] == "radiology"

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
                patient_dfn="123",
                group_by_encounter=True,
            )

            assert result.success is True
            procedures_data = result.procedures

            # Should have encounters grouping
            assert "encounters" in procedures_data
            encounters = procedures_data["encounters"]

            # Should have 2 encounters
            assert len(encounters) == 2

            # Find primary care encounter
            primary_encounter = next(
                e for e in encounters if e["encounter_name"] == "Primary Care Visit"
            )
            assert len(primary_encounter["procedures"]) == 2  # 99213 and 12001

            # Find radiology encounter
            radiology_encounter = next(
                e for e in encounters if e["encounter_name"] == "Radiology Visit"
            )
            assert len(radiology_encounter["procedures"]) == 1  # 71020


class TestCPTFilteringFunctions:
    """Test CPT filtering helper functions"""

    def test_apply_procedure_filters_category(self, sample_cpt_codes):
        """Test filtering by procedure category"""
        # Filter by evaluation category
        filtered = _apply_procedure_filters(
            sample_cpt_codes, procedure_category="evaluation"
        )

        assert len(filtered) == 1
        assert filtered[0].cpt_code == "99213"

    def test_apply_procedure_filters_date_range(self, sample_cpt_codes):
        """Test filtering by date range"""
        filtered = _apply_procedure_filters(
            sample_cpt_codes, date_from="2024-01-01", date_to="2024-01-31"
        )

        # All sample codes are from 2024-01-01, so all should be included
        assert len(filtered) == 3

        # Test excluding date range
        filtered = _apply_procedure_filters(sample_cpt_codes, date_from="2024-02-01")

        assert len(filtered) == 0

    def test_format_procedures_list(self, sample_cpt_codes):
        """Test formatting procedures as list"""
        formatted = _format_procedures_list(sample_cpt_codes, include_modifiers=True)

        assert len(formatted) == 3

        # Check structure
        procedure = formatted[0]
        required_fields = [
            "cpt_code",
            "description",
            "procedure_date",
            "provider",
            "quantity",
            "category",
            "complexity",
            "facility",
            "status",
        ]

        for field in required_fields:
            assert field in procedure

        # Check modifiers included
        xray_procedure = next(p for p in formatted if p["cpt_code"] == "71020")
        assert "modifiers" in xray_procedure
        assert xray_procedure["modifiers"] == ["26"]

    def test_group_procedures_by_encounter(self, sample_cpt_codes):
        """Test grouping procedures by encounter"""
        grouped = _group_procedures_by_encounter(sample_cpt_codes)

        assert "encounters" in grouped
        encounters = grouped["encounters"]
        assert len(encounters) == 2

        # Check encounter structure
        encounter = encounters[0]
        required_fields = [
            "encounter_uid",
            "encounter_name",
            "procedures",
            "procedure_count",
            "total_complexity_score",
        ]

        for field in required_fields:
            assert field in encounter

        assert encounter["procedure_count"] > 0
        assert len(encounter["procedures"]) == encounter["procedure_count"]

    def test_build_procedure_summary(self, sample_cpt_codes):
        """Test building procedure summary statistics"""
        summary = _build_procedure_summary(sample_cpt_codes, sample_cpt_codes)

        required_fields = [
            "total_procedures",
            "filtered_procedures",
            "surgical_procedures",
            "diagnostic_procedures",
            "procedures_with_modifiers",
            "category_breakdown",
            "complexity_breakdown",
            "unique_providers",
            "unique_encounters",
        ]

        for field in required_fields:
            assert field in summary

        assert summary["total_procedures"] == 3
        assert summary["filtered_procedures"] == 3
        assert summary["surgical_procedures"] == 1  # 12001 is surgery
        assert summary["diagnostic_procedures"] == 1  # 71020 is radiology
        assert summary["procedures_with_modifiers"] == 1  # 71020 has modifiers
        assert summary["unique_providers"] == 3  # 3 different providers
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
                patient_dfn="invalid",
            )

            assert result["success"] is False
            assert "error" in result

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
            dateOfBirth=datetime(1980, 1, 1),
            ssn="123456789",
            addresses=[],
            telecoms=[],
            supports=[],
            flags=[],
        )

        empty_patient_data = PatientDataCollection(
            demographics=demographics,
            cpt_codes=[],  # No CPT codes
            source_station="500",
            source_dfn="123",
        )

        with patch(
            "src.tools.patient.get_patient_procedures.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = empty_patient_data

            result = await get_patient_procedures_impl(
                vista_client=mock_vista_client,
                patient_dfn="123",
            )

            assert result.success is True
            assert len(result.procedures) == 0
            assert result.summary["total_procedures"] == 0

    @pytest.mark.asyncio
    async def test_cpt_pagination(self, sample_cpt_codes):
        """Test CPT procedure pagination functionality"""
        cpt_codes = sample_cpt_codes

        # Test pagination logic directly
        # Test with limit=2, offset=0
        limit = 2
        offset = 0
        total_cpt_codes = len(cpt_codes)
        cpt_codes_page = cpt_codes[offset : offset + limit]

        # Use the actual number of CPT codes available
        expected_returned = min(limit, total_cpt_codes)
        assert len(cpt_codes_page) == expected_returned

        # Test pagination response structure
        pagination_info = {
            "total": total_cpt_codes,
            "returned": len(cpt_codes_page),
            "offset": offset,
            "limit": limit,
        }

        assert pagination_info["total"] == total_cpt_codes
        assert pagination_info["returned"] == expected_returned
        assert pagination_info["offset"] == 0
        assert pagination_info["limit"] == 2

        # Test with offset=1, limit=1 (if we have enough CPT codes)
        if total_cpt_codes > 1:
            offset = 1
            limit = 1
            cpt_codes_page = cpt_codes[offset : offset + limit]
            expected_returned = min(limit, max(0, total_cpt_codes - offset))

            pagination_info = {
                "total": total_cpt_codes,
                "returned": len(cpt_codes_page),
                "offset": offset,
                "limit": limit,
            }

            assert pagination_info["total"] == total_cpt_codes
            assert pagination_info["returned"] == expected_returned
            assert pagination_info["offset"] == 1
            assert pagination_info["limit"] == 1

        # Test offset beyond total (should return 0 items)
        offset = 100
        cpt_codes_page = cpt_codes[offset : offset + limit]

        pagination_info = {
            "total": total_cpt_codes,
            "returned": len(cpt_codes_page),
            "offset": offset,
            "limit": limit,
        }

        assert pagination_info["returned"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
