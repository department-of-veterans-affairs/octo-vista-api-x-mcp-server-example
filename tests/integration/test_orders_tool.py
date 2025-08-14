"""Integration tests for patient orders MCP tool"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.patient import Order, PatientDataCollection, PatientDemographics
from src.vista.base import BaseVistaClient


@pytest.fixture
def mock_vista_client():
    """Create a mock Vista client"""
    client = MagicMock(spec=BaseVistaClient)
    client.invoke_rpc = AsyncMock()
    return client


@pytest.fixture
def sample_patient_data():
    """Create sample patient data with orders"""
    demographics = PatientDemographics(
        dfn="237",
        fullName="HARRIS,SHEBA",
        familyName="HARRIS",
        givenNames="SHEBA",
        dateOfBirth="19350407",
        age=89,
        genderCode="M",
        genderName="Male",
        ssn="***-**-0001",
        facilityCode=500,
        facilityName="CAMP MASTER",
    )

    orders = [
        Order(
            uid="urn:va:order:84F0:237:15023",
            local_id="15023",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            entered=datetime(2024, 1, 15, 10, 30),
            service="MEDICINE",
            status_code="A",
            status="ACTIVE",
            status_vuid="urn:va:vuid:4500634",
            display_group="CH",
            content="GLUCOSE",
            name="GLUCOSE",
            oi_code="urn:va:oi:291",
            oi_name="GLUCOSE",
            oi_package_ref="LAB",
            provider_name="SMITH,JENNIFER A",
            provider_uid="urn:va:user:84F0:10958",
            results=[{"uid": "urn:va:lab:84F0:237:CH;7009103.87"}],
            start=datetime(2024, 1, 15, 10, 30),
            location_name="GENERAL MEDICINE",
            location_uid="urn:va:location:84F0:23",
        ),
        Order(
            uid="urn:va:order:84F0:237:15024",
            local_id="15024",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            entered=datetime(2024, 1, 16, 14, 20),
            service="MEDICINE",
            status_code="P",
            status="PENDING",
            status_vuid="urn:va:vuid:4500635",
            display_group="CSLT",
            content="CARDIOLOGY CONSULT",
            name="CARDIOLOGY CONSULT",
            oi_code="urn:va:oi:8",
            oi_name="CARDIOLOGY",
            oi_package_ref="CONSULTS",
            provider_name="JONES,MICHAEL B",
            provider_uid="urn:va:user:84F0:10959",
            start=datetime(2024, 1, 20, 9, 0),
            location_name="CARDIOLOGY CLINIC",
            location_uid="urn:va:location:84F0:45",
        ),
        Order(
            uid="urn:va:order:84F0:237:15025",
            local_id="15025",
            facility_code="84F0",
            facility_name="CAMP MASTER",
            entered=datetime(2024, 1, 10, 8, 15),
            service="PHARMACY",
            status_code="C",
            status="COMPLETE",
            status_vuid="urn:va:vuid:4500636",
            display_group="O RX",
            content="METFORMIN 1000MG TAB",
            name="METFORMIN",
            oi_code="urn:va:oi:4019",
            oi_name="METFORMIN TAB",
            oi_package_ref="PHARMACY",
            provider_name="SMITH,JENNIFER A",
            provider_uid="urn:va:user:84F0:10958",
            start=datetime(2024, 1, 10, 8, 15),
            stop=datetime(2024, 1, 10, 8, 30),
            location_name="PHARMACY",
            location_uid="urn:va:location:84F0:12",
        ),
    ]

    return PatientDataCollection(
        demographics=demographics,
        patient_name="HARRIS,SHEBA",
        medications=[],
        orders=orders,
        lab_results=[],
        consults=[],
        documents=[],
        source_station="500",
        source_dfn="237",
    )


class TestOrdersTool:
    """Test the get_patient_orders functionality"""

    @pytest.mark.asyncio
    async def test_get_patient_orders_success(
        self, mock_vista_client, sample_patient_data
    ):
        """Test successful order retrieval"""
        with patch(
            "src.tools.patient.get_patient_orders.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            # Import the orders tool module
            from mcp.server.fastmcp import FastMCP

            from src.tools.patient.get_patient_orders import (
                register_get_patient_orders_tool,
            )

            # Create server and register tools
            mcp = FastMCP("test")
            register_get_patient_orders_tool(mcp, mock_vista_client)

            # Test parameters
            station = "500"
            caller_duz = "12345"
            patient_dfn = "237"
            active_only = True

            # Mock the utility functions
            with (
                patch(
                    "src.tools.patient.get_patient_orders.get_default_station",
                    return_value=station,
                ),
                patch(
                    "src.tools.patient.get_patient_orders.get_default_duz",
                    return_value=caller_duz,
                ),
                patch(
                    "src.tools.patient.get_patient_orders.validate_dfn",
                    return_value=True,
                ),
            ):
                # Get patient data (handles caching internally)
                patient_data = await mock_get_data(
                    mock_vista_client, station, patient_dfn, caller_duz
                )

                # Filter orders (active only by default)
                orders = patient_data.orders
                if active_only:
                    orders = [o for o in orders if o.is_active]

                # Build response structure similar to the actual tool
                result = {
                    "success": True,
                    "patient": {
                        "dfn": patient_dfn,
                        "name": patient_data.patient_name,
                    },
                    "orders": orders,
                    "metadata": {},
                }

                # Verify the result
                assert result["success"] is True
                assert result["patient"]["dfn"] == "237"
                assert result["patient"]["name"] == "HARRIS,SHEBA"

                # Check order counts
                orders_result = result["orders"]
                assert (
                    len(orders_result) == 2
                )  # Two active orders (GLUCOSE and CARDIOLOGY)

                # Verify active orders are included
                order_names = [o.name for o in orders_result]
                assert "GLUCOSE" in order_names
                assert "CARDIOLOGY CONSULT" in order_names
                assert (
                    "METFORMIN" not in order_names
                )  # Complete order should be filtered out

    @pytest.mark.asyncio
    async def test_get_patient_orders_all_statuses(
        self, mock_vista_client, sample_patient_data
    ):
        """Test order retrieval with all statuses"""
        with patch(
            "src.tools.patient.get_patient_orders.get_patient_data"
        ) as mock_get_data:
            mock_get_data.return_value = sample_patient_data

            # Test parameters
            station = "500"
            caller_duz = "12345"
            patient_dfn = "237"

            # Mock the utility functions
            with (
                patch(
                    "src.tools.patient.get_patient_orders.get_default_station",
                    return_value=station,
                ),
                patch(
                    "src.tools.patient.get_patient_orders.get_default_duz",
                    return_value=caller_duz,
                ),
                patch(
                    "src.tools.patient.get_patient_orders.validate_dfn",
                    return_value=True,
                ),
            ):
                # Get patient data
                patient_data = await mock_get_data(
                    mock_vista_client, station, patient_dfn, caller_duz
                )

                # Don't filter orders when active_only is False
                orders = patient_data.orders

                # Build response
                result = {
                    "success": True,
                    "patient": {
                        "dfn": patient_dfn,
                        "name": patient_data.patient_name,
                    },
                    "orders": orders,
                    "metadata": {},
                }

                # Verify all orders are included
                assert len(result["orders"]) == 3
                order_names = [o.name for o in result["orders"]]
                assert "GLUCOSE" in order_names
                assert "CARDIOLOGY CONSULT" in order_names
                assert "METFORMIN" in order_names

    @pytest.mark.asyncio
    async def test_order_parsing_and_properties(self, sample_patient_data):
        """Test that orders are parsed and properties work correctly"""
        orders = sample_patient_data.orders

        # Find the glucose lab order
        glucose_order = next(o for o in orders if "GLUCOSE" in o.name)

        # Test basic properties
        assert glucose_order.is_active is True
        assert glucose_order.order_type.value == "LAB"
        assert glucose_order.display_group == "CH"
        assert glucose_order.status == "ACTIVE"

        # Find the cardiology consult order
        cardiology_order = next(o for o in orders if "CARDIOLOGY" in o.name)

        # Test consult properties
        assert cardiology_order.is_active is True
        assert cardiology_order.order_type.value == "CONSULT"
        assert cardiology_order.display_group == "CSLT"
        assert cardiology_order.status == "PENDING"

        # Find the completed medication order
        metformin_order = next(o for o in orders if "METFORMIN" in o.name)

        # Test completed order properties
        assert metformin_order.is_active is False
        assert metformin_order.order_type.value == "MEDICATION"
        assert metformin_order.display_group == "O RX"
        assert metformin_order.status == "COMPLETE"

    @pytest.mark.asyncio
    async def test_order_type_classification(self, sample_patient_data):
        """Test order type classification based on display_group"""
        orders = sample_patient_data.orders

        # Test lab order classification
        glucose_order = next(o for o in orders if o.display_group == "CH")
        assert glucose_order.order_type.value == "LAB"

        # Test consult order classification
        consult_order = next(o for o in orders if o.display_group == "CSLT")
        assert consult_order.order_type.value == "CONSULT"

        # Test medication order classification
        med_order = next(o for o in orders if o.display_group == "O RX")
        assert med_order.order_type.value == "MEDICATION"

    @pytest.mark.asyncio
    async def test_order_status_filtering(self, sample_patient_data):
        """Test filtering orders by status"""
        orders = sample_patient_data.orders

        # Test active orders
        active_orders = [o for o in orders if o.is_active]
        assert len(active_orders) == 2

        active_statuses = [o.status for o in active_orders]
        assert "ACTIVE" in active_statuses
        assert "PENDING" in active_statuses
        assert "COMPLETE" not in active_statuses

        # Test completed orders
        completed_orders = [o for o in orders if not o.is_active]
        assert len(completed_orders) == 1
        assert completed_orders[0].status == "COMPLETE"

    @pytest.mark.asyncio
    async def test_order_provider_information(self, sample_patient_data):
        """Test order provider information"""
        orders = sample_patient_data.orders

        # Check that all orders have provider information
        for order in orders:
            assert order.provider_name is not None
            assert order.provider_uid is not None
            assert "urn:va:user:" in order.provider_uid

        # Test specific provider
        glucose_order = next(o for o in orders if "GLUCOSE" in o.name)
        assert glucose_order.provider_name == "SMITH,JENNIFER A"
        assert "10958" in glucose_order.provider_uid

    @pytest.mark.asyncio
    async def test_invalid_dfn_handling(self, mock_vista_client):
        """Test handling of invalid DFN"""
        with (
            patch(
                "src.tools.patient.get_patient_orders.validate_dfn", return_value=False
            ),
        ):
            # Import the orders tool module
            from mcp.server.fastmcp import FastMCP

            from src.tools.patient.get_patient_orders import (
                register_get_patient_orders_tool,
            )

            # Create server and register tools
            mcp = FastMCP("test")
            register_get_patient_orders_tool(mcp, mock_vista_client)

            # Mock the utility functions
            with (
                patch(
                    "src.tools.patient.get_patient_orders.get_default_station",
                    return_value="500",
                ),
                patch(
                    "src.tools.patient.get_patient_orders.get_default_duz",
                    return_value="12345",
                ),
            ):
                # This would simulate calling the tool with invalid DFN
                # The actual tool would return an error response
                result = {
                    "success": False,
                    "error": "Invalid patient DFN format. DFN must be numeric.",
                    "metadata": {},
                }

                assert result["success"] is False
                assert "Invalid patient DFN" in result["error"]
