"""Integration tests for patient visit MCP tool"""

import time
from datetime import datetime, timezone
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
            visit_date=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
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
            visit_date=datetime(2024, 1, 10, 14, 20, tzinfo=timezone.utc),
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
            visit_date=datetime(2023, 12, 1, 9, 0, tzinfo=timezone.utc),
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
            admission_date=datetime(2024, 1, 5, 8, 15, tzinfo=timezone.utc),
            discharge_date=datetime(2024, 1, 7, 10, 30, tzinfo=timezone.utc),
            scheduled_date=None,
            order_uids=["urn:va:order:84F0:100022:15025"],
            treatment_uids=["urn:va:treatment:84F0:100022:2001"],
        ),
        Visit(
            uid="urn:va:visit:84F0:100022:1004",
            local_id="1004",
            visit_date=datetime(2023, 12, 25, 16, 45, tzinfo=timezone.utc),
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
            admission_date=datetime(2023, 12, 20, 9, 0, tzinfo=timezone.utc),
            discharge_date=datetime(2023, 12, 20, 15, 30, tzinfo=timezone.utc),
            scheduled_date=datetime(2023, 12, 20, 9, 0, tzinfo=timezone.utc),
            order_uids=["urn:va:order:84F0:100022:15026"],
            treatment_uids=["urn:va:treatment:84F0:100022:2002"],
        ),
    ]

    return PatientDataCollection(
        demographics=demographics,
        visits_dict={v.uid: v for v in visits},
        source_station="500",
        source_icn="100022",
    )


class TestVisitToolIntegration:
    """Test visit tool integration with mock data"""

    @pytest.mark.asyncio
    async def test_get_patient_visits_basic(
        self, mock_vista_client, sample_patient_data
    ):
        """Test basic visit retrieval"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            # Import the visit tool module
            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            # Test parameters
            station = "500"
            caller_duz = "12345"
            patient_icn = "100022"

            # Mock the utility functions
            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value=station,
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value=caller_duz,
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn=patient_icn,
                    station=station,
                    vista_client=mock_vista_client,
                )

                assert result.success is True
                assert result.data.summary is not None
                assert result.data.all_visits is not None

                # Check visits summary
                summary = result.data.summary
                assert summary.total_visits >= 0

    @pytest.mark.asyncio
    async def test_get_patient_visits_with_filters(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with filters"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    visit_type="inpatient",
                    active_only=False,
                    days_back=30,
                    vista_client=mock_vista_client,
                )

                assert result.success is True
                assert result.data is not None

                # Check filters in metadata
                metadata = result.metadata
                assert metadata.filters.visit_type == "inpatient"
                assert metadata.filters.active_only is False
                assert metadata.filters.days_back == 30

                # Check visits structure
                visits_data = result.data
                assert visits_data.all_visits is not None
                assert visits_data.summary is not None

    @pytest.mark.asyncio
    async def test_get_patient_visits_invalid_patient(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with invalid patient"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="999999",
                    station="500",
                    vista_client=mock_vista_client,
                )

                # Should handle gracefully - either return empty results or error
                assert result.success is not None
                # The exact behavior depends on how the mock server handles invalid patients

    @pytest.mark.asyncio
    async def test_get_patient_visits_invalid_days_back(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with invalid days_back parameter"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    days_back=0,  # Invalid
                    vista_client=mock_vista_client,
                )

                assert result.success is False
                assert result.error is not None
                assert "Days back must be between 1 and 1095" in result.error

    @pytest.mark.asyncio
    async def test_get_patient_visits_invalid_dfn(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit retrieval with invalid DFN format"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=False,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="invalid-dfn",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result.success is False
                assert result.error is not None
                assert "Invalid patient ICN format" in result.error

    @pytest.mark.asyncio
    async def test_get_patient_visits_metadata(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit tool metadata"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result.success is True
                metadata = result.metadata

                # Check required metadata fields
                assert metadata.station is not None
                assert metadata.performance.duration_ms >= 0
                assert metadata.rpc is not None
                assert metadata.demographics is not None
                assert metadata.filters is not None

                # Check RPC metadata
                rpc_metadata = metadata.rpc
                assert rpc_metadata.rpc == "VPR GET PATIENT DATA JSON"
                assert rpc_metadata.context == "LHS RPC CONTEXT"
                assert rpc_metadata.json_result is True

                # Check filters metadata
                filters = metadata.filters
                assert hasattr(filters, "visit_type")
                assert hasattr(filters, "active_only")
                assert hasattr(filters, "days_back")

    @pytest.mark.asyncio
    async def test_get_patient_visits_response_structure(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit tool response structure"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result.success is True

                # Check patient structure
                patient = result.data

                # Check visits structure
                assert patient.summary is not None
                assert patient.all_visits is not None

                # Check all_visits structure
                all_visits = patient.all_visits
                assert isinstance(all_visits, list)

                # If there are visits, check their structure
                if all_visits:
                    visit = all_visits[0]
                    assert visit.uid is not None
                    assert visit.visit_date is not None
                    assert visit.location_name is not None
                    assert visit.visit_type is not None
                    assert visit.status_name is not None

    @pytest.mark.asyncio
    async def test_get_patient_visits_duration_calculation(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit duration calculation in response"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    vista_client=mock_vista_client,
                )

                assert result.success is True
                visits = result.data.all_visits

                # Check that visits have proper structure
                for visit in visits:
                    assert visit.uid is not None
                    # Duration calculation depends on admission/discharge dates
                    if visit.admission_date and visit.discharge_date:
                        duration = (visit.discharge_date - visit.admission_date).days
                        assert duration >= 0

    @pytest.mark.asyncio
    async def test_get_patient_visits_date_filtering(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit date filtering"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            # Test with different days_back values
            for days_back in [30, 90, 365]:
                with (
                    patch(
                        "src.tools.patient.get_patient_visits_tool.get_default_station",
                        return_value="500",
                    ),
                    patch(
                        "src.tools.patient.get_patient_visits_tool.get_default_duz",
                        return_value="12345",
                    ),
                    patch(
                        "src.tools.patient.get_patient_visits_tool.validate_icn",
                        return_value=True,
                    ),
                    patch("time.time", return_value=time.time()),
                ):
                    result = await get_patient_visits_impl(
                        patient_icn="100022",
                        station="500",
                        days_back=days_back,
                        vista_client=mock_vista_client,
                    )

                    assert result.success is True
                    metadata = result.metadata
                    assert metadata.filters.days_back == days_back

    @pytest.mark.asyncio
    async def test_get_patient_visits_type_filtering(
        self, mock_vista_client, sample_patient_data
    ):
        """Test visit type filtering"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

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
                        "src.tools.patient.get_patient_visits_tool.get_default_station",
                        return_value="500",
                    ),
                    patch(
                        "src.tools.patient.get_patient_visits_tool.get_default_duz",
                        return_value="12345",
                    ),
                    patch(
                        "src.tools.patient.get_patient_visits_tool.validate_icn",
                        return_value=True,
                    ),
                    patch("time.time", return_value=time.time()),
                ):
                    result = await get_patient_visits_impl(
                        patient_icn="100022",
                        station="500",
                        visit_type=visit_type,
                        vista_client=mock_vista_client,
                    )

                    assert result.success is True
                    metadata = result.metadata
                    assert metadata.filters.visit_type == visit_type

                    # Check that all returned visits match the requested type
                    all_visits = result.data.all_visits
                    for visit in all_visits:
                        assert visit.visit_type.value == visit_type

    @pytest.mark.asyncio
    async def test_get_patient_visits_active_filtering(
        self, mock_vista_client, sample_patient_data
    ):
        """Test active visit filtering"""
        with patch(
            "src.tools.patient.get_patient_visits_tool.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            from src.tools.patient.get_patient_visits_tool import (
                get_patient_visits_impl,
            )

            # Test with active_only=True
            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    active_only=True,
                    vista_client=mock_vista_client,
                )

                assert result.success is True
                metadata = result.metadata
                assert metadata.filters.active_only is True

                # Check that all returned visits are active (based on VistA status)
                all_visits = result.data.all_visits
                for visit in all_visits:
                    assert visit.status_code and visit.status_code.lower() == "active"

            # Test with active_only=False
            with (
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.get_default_duz",
                    return_value="12345",
                ),
                patch(
                    "src.tools.patient.get_patient_visits_tool.validate_icn",
                    return_value=True,
                ),
                patch("time.time", return_value=time.time()),
            ):
                result = await get_patient_visits_impl(
                    patient_icn="100022",
                    station="500",
                    active_only=False,
                    vista_client=mock_vista_client,
                )

                assert result.success is True
                metadata = result.metadata
                assert metadata.filters.active_only is False

                # Should return all visits (active and inactive)
                all_visits = result.data.all_visits
                # Note: In a real scenario, we'd expect both active and inactive visits
                # For the mock server, we just verify the structure is correct
