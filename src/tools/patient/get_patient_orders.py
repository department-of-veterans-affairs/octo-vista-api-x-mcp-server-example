"""Get patient orders tool"""

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_orders_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_orders tool with the MCP server"""

    @mcp.tool()
    async def get_patient_orders(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieve orders for a specific patient

        Orders include medications, labs, procedures, and consults

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)
            active_only: When True, returns only pending/active/scheduled orders;
                        when False, includes complete and discontinued orders (default: True)

        Returns:
            Order data including:
            - type of order: medication, lab, or consult
            - order status: pending, active, complete, discontinued
            - for lab orders
            -- name of lab
            -- VA orderable item (OI) code
            -- URNs of lab results if available
            - for medication orders
            -- medication name and dosage in a single string 'content'
            -- URN of medication item if available
            -- VA orderable item (OI) code
            -- A flag 'nonVA' indicating if the order is from a non-VA pharmacy
            - for consult orders
            -- Description of the consult purpose as 'content'
            -- Consulting clinicians
            - for all orders, requesting and consulting provider information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        logger.info(
            f"🩺 [DEBUG] get_patient_orders: patient_dfn={patient_dfn}, station={station}, active_only={active_only}"
        )
        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter orders
            orders = patient_data.orders
            if active_only:
                orders = [o for o in orders if o.is_active]

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                },
                "orders": orders,
                "metadata": {
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_orders")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
