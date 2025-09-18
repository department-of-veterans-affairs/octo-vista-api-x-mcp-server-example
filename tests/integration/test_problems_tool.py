"""Integration tests for get_patient_problems tool."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.models.patient.collection import PatientDataCollection
from src.models.patient.demographics import PatientDemographics
from src.models.patient.problem import Problem, ProblemStatus
from src.models.responses.tool_responses import ProblemsResponse
from src.vista.base import BaseVistaClient


@pytest.fixture
def mock_vista_client():
    """Create a mock VistA client."""
    return MagicMock(spec=BaseVistaClient)


@pytest.fixture
def mock_patient_data():
    """Create mock patient data with problems."""
    # Create mock demographics
    demographics = PatientDemographics(
        uid="urn:va:patient:84F0:237",
        dfn="237",
        pid="84F0;237",
        icn="1008684701V329302",
        fullName="PATIENT,TEST",
        familyName="PATIENT",
        givenNames="TEST",
        displayName="PATIENT,TEST",
        genderCode="M",
        genderName="Male",
        dateOfBirth=datetime(1935, 4, 7, tzinfo=UTC).date(),
        ssn="666001001",
        sensitive=False,
        deceased=False,
    )

    # Create mock problems
    problems = [
        Problem(
            uid="urn:va:problem:84F0:237:2001",
            localId="2001",
            problemText="Former heavy tobacco smoker (SCT 428081000124100)",
            statusCode="urn:sct:55561003",
            statusName=ProblemStatus.ACTIVE,
            icdCode="urn:10d:Z87.891",
            icdName="Personal history of nicotine dependence",
            entered=datetime(2025, 7, 14, tzinfo=UTC),
            updated=datetime(2025, 7, 14, tzinfo=UTC),
            providerName="ARKORFUL,NANA",
            providerUid="urn:va:user:84F0:520824797",
            facilityCode="500",
            facilityName="CAMP MASTER",
            locationName="CARDIOLOGY",
            locationUid="urn:va:location:84F0:195",
            serviceConnected=False,
            removed=False,
            unverified=False,
        ),
        Problem(
            uid="urn:va:problem:84F0:237:2002",
            localId="2002",
            problemText="Hypertensive heart and chronic kidney disease (SCT 8501000119104)",
            statusCode="urn:sct:55561003",
            statusName=ProblemStatus.ACTIVE,
            icdCode="urn:10d:I13.10",
            icdName="Hyp hrt & chr kdny dis w/o hrt fail, w stg 1-4/unsp chr kdny",
            entered=datetime(2025, 7, 14, tzinfo=UTC),
            updated=datetime(2025, 7, 14, tzinfo=UTC),
            providerName="CHERIATHUNDAM,JACOB P",
            providerUid="urn:va:user:84F0:520824840",
            facilityCode="500",
            facilityName="CAMP MASTER",
            locationName="CARDIOLOGY",
            locationUid="urn:va:location:84F0:195",
            serviceConnected=True,
            serviceConnectionPercent=75,
            removed=False,
            unverified=False,
        ),
        Problem(
            uid="urn:va:problem:84F0:237:268",
            localId="268",
            problemText="Myocardial infarction (SCT 22298006)",
            statusCode="urn:sct:73425007",
            statusName=ProblemStatus.INACTIVE,
            icdCode="urn:icd:410.90",
            icdName="AMI NOS, UNSPECIFIED",
            entered=datetime(2024, 5, 23, tzinfo=UTC),
            updated=datetime(2024, 3, 30, tzinfo=UTC),
            providerName="VEHU,ONE",
            providerUid="urn:va:user:84F0:20001",
            facilityCode="500",
            facilityName="CAMP MASTER",
            service="MEDICINE",
            serviceConnected=False,
            removed=False,
            unverified=False,
        ),
    ]

    # Create patient data collection
    return PatientDataCollection(
        demographics=demographics,
        problems_dict={problem.uid: problem for problem in problems},
        source_station="84F0",
        source_icn="237",
        total_items=3,
    )


@pytest.fixture
def mock_get_patient_data(mock_patient_data):
    """Mock the get_patient_data function."""

    async def _mock_get_patient_data(vista_client, station, dfn, duz):
        return mock_patient_data

    return _mock_get_patient_data


class TestGetPatientProblemsToolIntegration:
    """Integration tests for get_patient_problems tool."""

    @pytest.mark.asyncio
    async def test_get_patient_problems_success(
        self, mock_vista_client, mock_get_patient_data, monkeypatch
    ):
        """Test successful retrieval of patient problems."""
        # Mock the get_patient_data function
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_patient_data",
            mock_get_patient_data,
        )

        # Mock validation functions
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.validate_icn", lambda dfn: True
        )
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_default_station",
            lambda: "84F0",
        )
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_default_duz", lambda: "123"
        )

        # Import the tool function directly
        from src.tools.patient.get_patient_problems_tool import (
            register_get_patient_problems_tool,
        )

        # Create a simple mock MCP to capture the registered function
        registered_func = None

        class MockMCP:
            def tool(self, name=None, description=None):
                def decorator(func):
                    nonlocal registered_func
                    registered_func = func
                    return func

                return decorator

        mock_mcp = MockMCP()
        register_get_patient_problems_tool(mock_mcp, mock_vista_client)

        # Call the tool function
        result = await registered_func(
            patient_icn="237",
            station="84F0",
            active_only=False,
            service_connected_only=False,
            days_back=36500,  # 100 years to include all test data
            offset=0,
            limit=10,
        )

        # Verify response
        assert isinstance(result, ProblemsResponse)
        assert result.success is True
        assert result.data is not None
        assert len(result.data.problems) == 3
        assert result.data.summary.total_problems == 3
        assert result.data.summary.active_count == 2
        assert result.data.summary.inactive_count == 1
        assert result.data.summary.service_connected_count == 1

    @pytest.mark.asyncio
    async def test_get_patient_problems_with_active_filter(
        self, mock_vista_client, mock_get_patient_data, monkeypatch
    ):
        """Test retrieval with active_only filter."""
        # Mock the get_patient_data function
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_patient_data",
            mock_get_patient_data,
        )

        # Mock validation functions
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.validate_icn", lambda dfn: True
        )
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_default_station",
            lambda: "84F0",
        )
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_default_duz", lambda: "123"
        )

        # Import the tool function directly
        from src.tools.patient.get_patient_problems_tool import (
            register_get_patient_problems_tool,
        )

        # Create a simple mock MCP to capture the registered function
        registered_func = None

        class MockMCP:
            def tool(self, name=None, description=None):
                def decorator(func):
                    nonlocal registered_func
                    registered_func = func
                    return func

                return decorator

        mock_mcp = MockMCP()
        register_get_patient_problems_tool(mock_mcp, mock_vista_client)

        # Call the tool with active_only filter
        result = await registered_func(
            patient_icn="237",
            station="84F0",
            active_only=True,
            service_connected_only=False,
            days_back=365,
            offset=0,
            limit=10,
        )

        # Verify response - should only return active problems
        assert isinstance(result, ProblemsResponse)
        assert result.success is True
        assert result.data is not None
        assert len(result.data.problems) == 2  # Only active problems
        assert result.data.summary.active_count == 2
        assert result.data.summary.inactive_count == 0
        assert all(problem.is_active for problem in result.data.problems)

    @pytest.mark.asyncio
    async def test_get_patient_problems_invalid_dfn(
        self, mock_vista_client, monkeypatch
    ):
        """Test handling of invalid DFN."""
        # Mock validation functions
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.validate_icn",
            lambda dfn: False,  # Invalid DFN
        )
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_default_station",
            lambda: "84F0",
        )
        monkeypatch.setattr(
            "src.tools.patient.get_patient_problems_tool.get_default_duz", lambda: "123"
        )

        # Import the tool function directly
        from src.tools.patient.get_patient_problems_tool import (
            register_get_patient_problems_tool,
        )

        # Create a simple mock MCP to capture the registered function
        registered_func = None

        class MockMCP:
            def tool(self, name=None, description=None):
                def decorator(func):
                    nonlocal registered_func
                    registered_func = func
                    return func

                return decorator

        mock_mcp = MockMCP()
        register_get_patient_problems_tool(mock_mcp, mock_vista_client)

        # Call the tool with invalid DFN
        result = await registered_func(
            patient_icn="invalid",
            station="84F0",
            active_only=False,
            service_connected_only=False,
            days_back=365,
            offset=0,
            limit=10,
        )

        # Verify error response
        assert isinstance(result, ProblemsResponse)
        assert result.success is False
        assert result.error is not None
        assert "Invalid patient ICN" in result.error
        assert result.data is None
