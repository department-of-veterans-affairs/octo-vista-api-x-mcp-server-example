"""Get patient orders tool"""

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.responses.tool_responses import PatientInfo, PatientOrdersResponse
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import (
    build_metadata,
    build_pagination_metadata,
    get_default_duz,
    get_default_station,
    get_logger,
)
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_orders_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_orders tool with the MCP server"""

    @mcp.tool()
    async def get_patient_orders(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> PatientOrdersResponse | dict[str, Any]:
        """Get patient orders including medications, labs, and procedures."""
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

            # Apply pagination
            total_orders = len(orders)
            orders_page = orders[offset : offset + limit]

            # Build response
            return PatientOrdersResponse(
                success=True,
                patient=PatientInfo(
                    dfn=patient_dfn,
                    name=patient_data.patient_name,
                ),
                orders={
                    "count": len(orders_page),
                    "total_filtered": total_orders,
                    "items": orders_page,
                },
                pagination=build_pagination_metadata(
                    total_items=total_orders,
                    returned_items=len(orders_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_orders",
                    patient_dfn=patient_dfn,
                    station=station,
                    active_only=active_only,
                ),
                metadata={
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
            )

        except Exception as e:
            logger.exception("Unexpected error in get_patient_orders")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
