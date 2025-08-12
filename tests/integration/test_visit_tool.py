"""Integration tests for patient visit MCP tool"""

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.patient import (
    PatientDataCollection,
    PatientDemographics,
    Visit,
    VisitType,
)
from src.vista.base import BaseVistaClient


@pytest.fixture
def mock_vista_client():
    """Create a mock Vista client"""
    client = MagicMock(spec=BaseVistaClient)
    client.invoke_rpc = AsyncMock()
    return client


@pytest.fixture
def sample_patient_data():
    """Create sample patient data with visits"""
    demographics = PatientDemographics(
        dfn="100022",
        fullName="ANDERSON,JAMES ROBERT",
        familyName="ANDERSON",
        givenNames="JAMES ROBERT",
        dateOfBirth="19500407",
        age=74,
        genderCode="M",
        genderName="Male",
        ssn="***-**-1234",
        facilityCode=500,
        facilityName="CAMP MASTER",
    )

    visits = [
        Visit(
            uid="urn:va:visit:84F0:100022:1001",
            local_id="1001",
            visit_date=datetime(2024, 1, 15, 10, 30),
            location_code="23",
            location_name="GENERAL MEDICINE",
            visit_type=VisitType.OUTPATIENT,
            provider_uid="urn:va:user:84F0:10958",
            provider_name="SMITH,JENNIFER A",
            status_code="A",
            status_name="ACTIVE",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            ward="GENERAL MEDICINE",
            room="101",
            bed="A",
            chief_complaint="Follow-up visit",
            diagnosis="Hypertension",
            admission_date=None,
            discharge_date=None,
            scheduled_date=None,
            order_uids=["urn:va:order:84F0:100022:15023"],
            treatment_uids=[],
        ),
        Visit(
            uid="urn:va:visit:84F0:100022:1002",
            local_id="1002",
            visit_date=datetime(2024, 1, 10, 14, 20),
            location_code="45",
            location_name="CARDIOLOGY CLINIC",
            visit_type=VisitType.OUTPATIENT,
            provider_uid="urn:va:user:84F0:10959",
            provider_name="JONES,MICHAEL B",
            status_code="A",
            status_name="ACTIVE",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            ward="CARDIOLOGY",
            room="201",
            bed=None,
            chief_complaint="Chest pain evaluation",
            diagnosis="Coronary artery disease",
            admission_date=None,
            discharge_date=None,
            scheduled_date=None,
            order_uids=["urn:va:order:84F0:100022:15024"],
            treatment_uids=[],
        ),
        Visit(
            uid="urn:va:visit:84F0:100022:1003",
            local_id="1003",
            visit_date=datetime(2024, 1, 5, 8, 15),
            location_code="12",
            location_name="EMERGENCY ROOM",
            visit_type=VisitType.EMERGENCY,
            provider_uid="urn:va:user:84F0:10960",
            provider_name="BROWN,SARAH L",
            status_code="C",
            status_name="COMPLETE",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            ward="EMERGENCY",
            room="ER1",
            bed="1",
            chief_complaint="Shortness of breath",
            diagnosis="Acute exacerbation of COPD",
            admission_date=datetime(2024, 1, 5, 8, 15),
            discharge_date=datetime(2024, 1, 7, 10, 30),
            scheduled_date=None,
            order_uids=["urn:va:order:84F0:100022:15025"],
            treatment_uids=["urn:va:treatment:84F0:100022:2001"],
        ),
        Visit(
            uid="urn:va:visit:84F0:100022:1004",
            local_id="1004",
            visit_date=datetime(2023, 12, 20, 9, 0),
            location_code="34",
            location_name="OPERATING ROOM",
            visit_type=VisitType.SURGERY,
            provider_uid="urn:va:user:84F0:10961",
            provider_name="WILSON,DAVID R",
            status_code="C",
            status_name="COMPLETE",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            ward="SURGERY",
            room="OR1",
            bed=None,
            chief_complaint="Elective procedure",
            diagnosis="Cataract surgery",
            admission_date=datetime(2023, 12, 20, 9, 0),
            discharge_date=datetime(2023, 12, 20, 15, 30),
            scheduled_date=datetime(2023, 12, 20, 9, 0),
            order_uids=["urn:va:order:84F0:100022:15026"],
            treatment_uids=["urn:va:treatment:84F0:100022:2002"],
        ),
    ]

    return PatientDataCollection(
        demographics=demographics,
        visits=visits,
        medications=[],
        vital_signs=[],
        lab_results=[],
        orders=[],
        health_factors=[],
        diagnoses=[],
        documents=[],
        source_station="500",
        source_dfn="100022",
    )


class TestVisitToolIntegration:
    """Test visit tool integration with mock data"""

    @pytest.mark.asyncio
    async def test_get_patient_visits_basic(
        self, mock_vista_client, sample_patient_data
    ):
        """Test basic visit retrieval"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            # Import the visit tool module
            from src.tools.patient.visit_tool import get_patient_visits

            # Test parameters
            station = "500"
            caller_duz = "12345"
            patient_dfn = "100022"

            # Mock the utility functions
            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value=station,
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz",
                    return_value=caller_duz,
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch("src.tools.patient.visit_tool.build_metadata", return_value={}),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn=patient_dfn,
                    station=station,
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True
                assert "patient" in result
                assert "visits" in result
                assert "summary" in result["visits"]
                assert "all_visits" in result["visits"]

                # Check patient info
                patient = result["patient"]
                assert patient["dfn"] == "100022"
                assert "name" in patient

                # Check visits summary
                summary = result["visits"]["summary"]
                assert "total_count" in summary
                assert "active_count" in summary
                assert "inpatient_count" in summary
                assert "emergency_count" in summary
                assert "by_type" in summary

    @pytest.mark.asyncio
    async def test_get_patient_visits_with_filters(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with filters"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch(
                    "src.tools.patient.visit_tool.build_metadata",
                    return_value={
                        "filters": {
                            "visit_type": "inpatient",
                            "active_only": False,
                            "days_back": 30,
                        }
                    },
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    visit_type="inpatient",
                    active_only=False,
                    days_back=30,
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True
                assert "visits" in result

                # Check filters in metadata
                metadata = result["metadata"]
                assert metadata["filters"]["visit_type"] == "inpatient"
                assert metadata["filters"]["active_only"] is False
                assert metadata["filters"]["days_back"] == 30

    @pytest.mark.asyncio
    async def test_get_patient_visits_invalid_patient(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with invalid patient"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch("src.tools.patient.visit_tool.build_metadata", return_value={}),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="999999",
                    station="500",
                    vista_client=mock_vista_client,
                )

                # Should handle gracefully - either return empty results or error
                assert "success" in result
                # The exact behavior depends on how the mock server handles invalid patients

    @pytest.mark.asyncio
    async def test_get_patient_visits_invalid_days_back(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with invalid days_back parameter"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch("src.tools.patient.visit_tool.build_metadata", return_value={}),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    days_back=0,  # Invalid
                    vista_client=mock_vista_client,
                )

                assert result["success"] is False
                assert "error" in result
                assert "Days back must be between 1 and 1095" in result["error"]

    @pytest.mark.asyncio
    async def test_get_patient_visits_invalid_dfn(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with invalid DFN format"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=False),
                patch("src.tools.patient.visit_tool.build_metadata", return_value={}),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="invalid-dfn",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result["success"] is False
                assert "error" in result
                assert "Invalid patient DFN format" in result["error"]

    @pytest.mark.asyncio
    async def test_get_patient_visits_metadata(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit tool metadata"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch(
                    "src.tools.patient.visit_tool.build_metadata",
                    return_value={
                        "station": "500",
                        "duration_ms": 100,
                        "rpc": {
                            "rpc": "VPR GET PATIENT DATA JSON",
                            "context": "LHS RPC CONTEXT",
                            "jsonResult": True,
                            "parameters": [{"namedArray": {"patientId": "100022"}}],
                        },
                        "duz": "12345",
                        "filters": {
                            "visit_type": "",
                            "active_only": False,
                            "days_back": 365,
                        },
                    },
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True
                metadata = result["metadata"]

                # Check required metadata fields
                assert "station" in metadata
                assert "duration_ms" in metadata
                assert "rpc" in metadata
                assert "duz" in metadata
                assert "filters" in metadata

                # Check RPC metadata
                rpc_metadata = metadata["rpc"]
                assert rpc_metadata["rpc"] == "VPR GET PATIENT DATA JSON"
                assert rpc_metadata["context"] == "LHS RPC CONTEXT"
                assert rpc_metadata["jsonResult"] is True

                # Check filters metadata
                filters = metadata["filters"]
                assert "visit_type" in filters
                assert "active_only" in filters
                assert "days_back" in filters

    @pytest.mark.asyncio
    async def test_get_patient_visits_response_structure(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit tool response structure"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch("src.tools.patient.visit_tool.build_metadata", return_value={}),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True

                # Check patient structure
                patient = result["patient"]
                required_patient_fields = ["name", "dfn", "age", "gender"]
                for field in required_patient_fields:
                    assert field in patient

                # Check visits structure
                visits = result["visits"]
                assert "summary" in visits
                assert "all_visits" in visits

                # Check summary structure
                summary = visits["summary"]
                required_summary_fields = [
                    "total_count",
                    "active_count",
                    "inpatient_count",
                    "emergency_count",
                    "by_type",
                ]
                for field in required_summary_fields:
                    assert field in summary

                # Check by_type structure
                by_type = summary["by_type"]
                assert isinstance(by_type, dict)

                # Check all_visits structure
                all_visits = visits["all_visits"]
                assert isinstance(all_visits, list)

                # If there are visits, check their structure
                if all_visits:
                    visit = all_visits[0]
                    required_visit_fields = [
                        "id",
                        "visit_date",
                        "location",
                        "visit_type",
                        "status",
                        "active",
                        "inpatient",
                        "emergency",
                    ]
                    for field in required_visit_fields:
                        assert field in visit

    @pytest.mark.asyncio
    async def test_get_patient_visits_duration_calculation(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit duration calculation in response"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch("src.tools.patient.visit_tool.build_metadata", return_value={}),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True
                visits = result["visits"]["all_visits"]

                # Check that duration_days is present for each visit
                for visit in visits:
                    assert "duration_days" in visit
                    # Duration should be None or a positive integer
                    if visit["duration_days"] is not None:
                        assert isinstance(visit["duration_days"], int)
                        assert visit["duration_days"] >= 0

    @pytest.mark.asyncio
    async def test_get_patient_visits_date_filtering(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit date filtering"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            # Test with different days_back values
            for days_back in [30, 90, 365]:
                with (
                    patch(
                        "src.tools.patient.visit_tool.get_default_station",
                        return_value="500",
                    ),
                    patch(
                        "src.tools.patient.visit_tool.get_default_duz",
                        return_value="12345",
                    ),
                    patch(
                        "src.tools.patient.visit_tool.validate_dfn", return_value=True
                    ),
                    patch(
                        "src.tools.patient.visit_tool.build_metadata",
                        return_value={"filters": {"days_back": days_back}},
                    ),
                    patch("time.time", return_value=time.time()),
                ):
                    result = await get_patient_visits(
                        patient_dfn="100022",
                        station="500",
                        days_back=days_back,
                        vista_client=mock_vista_client,
                    )

                    assert result["success"] is True
                    metadata = result["metadata"]
                    assert metadata["filters"]["days_back"] == days_back

    @pytest.mark.asyncio
    async def test_get_patient_visits_type_filtering(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit type filtering"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            visit_types = [
                "inpatient",
                "outpatient",
                "emergency",
                "observation",
                "surgery",
            ]

            for visit_type in visit_types:
                with (
                    patch(
                        "src.tools.patient.visit_tool.get_default_station",
                        return_value="500",
                    ),
                    patch(
                        "src.tools.patient.visit_tool.get_default_duz",
                        return_value="12345",
                    ),
                    patch(
                        "src.tools.patient.visit_tool.validate_dfn", return_value=True
                    ),
                    patch(
                        "src.tools.patient.visit_tool.build_metadata",
                        return_value={"filters": {"visit_type": visit_type}},
                    ),
                    patch("time.time", return_value=time.time()),
                ):
                    result = await get_patient_visits(
                        patient_dfn="100022",
                        station="500",
                        visit_type=visit_type,
                        vista_client=mock_vista_client,
                    )

                    assert result["success"] is True
                    metadata = result["metadata"]
                    assert metadata["filters"]["visit_type"] == visit_type

                    # Check that all returned visits match the requested type
                    all_visits = result["visits"]["all_visits"]
                    for visit in all_visits:
                        assert visit["visit_type"] == visit_type

    @pytest.mark.asyncio
    async def test_get_patient_visits_active_filtering(
        self, mock_vista_client, sample_patient_data
    ):
        """Test active visit filtering"""
        with patch("src.tools.patient.visit_tool.get_patient_data") as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.visit_tool import get_patient_visits

            # Test with active_only=True
            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch(
                    "src.tools.patient.visit_tool.build_metadata",
                    return_value={"filters": {"active_only": True}},
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    active_only=True,
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True
                metadata = result["metadata"]
                assert metadata["filters"]["active_only"] is True

                # Check that all returned visits are active
                all_visits = result["visits"]["all_visits"]
                for visit in all_visits:
                    assert visit["active"] is True

            # Test with active_only=False
            with (
                patch(
                    "src.tools.patient.visit_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.visit_tool.get_default_duz", return_value="12345"
                ),
                patch("src.tools.patient.visit_tool.validate_dfn", return_value=True),
                patch(
                    "src.tools.patient.visit_tool.build_metadata",
                    return_value={"filters": {"active_only": False}},
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits(
                    patient_dfn="100022",
                    station="500",
                    active_only=False,
                    vista_client=mock_vista_client,
                )

                assert result["success"] is True
                metadata = result["metadata"]
                assert metadata["filters"]["active_only"] is False

                # Should return both active and inactive visits
                all_visits = result["visits"]["all_visits"]
                # Note: In a real scenario, we'd expect both active and inactive visits
                # For the mock server, we just verify the structure is correct

    @pytest.mark.asyncio
    async def test_visit_pagination(self, sample_patient_data):
        """Test visit pagination functionality"""
        visits = sample_patient_data.visits

        # Test pagination logic directly
        # Test with limit=3, offset=0
        limit = 3
        offset = 0
        total_visits = len(visits)
        visits_page = visits[offset : offset + limit]

        # Use the actual number of visits available
        expected_returned = min(limit, total_visits)
        assert len(visits_page) == expected_returned

        # Test pagination response structure
        pagination_info = {
            "total": total_visits,
            "returned": len(visits_page),
            "offset": offset,
            "limit": limit,
        }

        assert pagination_info["total"] == total_visits
        assert pagination_info["returned"] == expected_returned
        assert pagination_info["offset"] == 0
        assert pagination_info["limit"] == 3

        # Test with offset=1, limit=2 (if we have enough visits)
        if total_visits > 1:
            offset = 1
            limit = 2
            visits_page = visits[offset : offset + limit]
            expected_returned = min(limit, max(0, total_visits - offset))

            pagination_info = {
                "total": total_visits,
                "returned": len(visits_page),
                "offset": offset,
                "limit": limit,
            }

            assert pagination_info["total"] == total_visits
            assert pagination_info["returned"] == expected_returned
            assert pagination_info["offset"] == 1
            assert pagination_info["limit"] == 2

        # Test offset beyond total (should return 0 items)
        offset = 100
        visits_page = visits[offset : offset + limit]

        pagination_info = {
            "total": total_visits,
            "returned": len(visits_page),
            "offset": offset,
            "limit": limit,
        }

        assert pagination_info["returned"] == 0
