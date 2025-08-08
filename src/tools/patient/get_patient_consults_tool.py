"""Get patient consults tool for MCP server"""

import time
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.formatters import format_service_name, format_status, format_urgency
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_consults_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_consults tool with the MCP server"""

    @mcp.tool()
    async def get_patient_consults(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """Get patient consultation requests and referrals."""
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

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

            # Filter consults
            consults = patient_data.consults
            if active_only:
                consults = [c for c in consults if c.is_active]

            # Get overdue consults
            overdue_consults = [c for c in consults if c.is_overdue]

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                },
                "consults": {
                    "total": len(patient_data.consults),
                    "active": len([c for c in patient_data.consults if c.is_active]),
                    "overdue": len(overdue_consults),
                    "filters": {
                        "active_only": active_only,
                    },
                    "overdue_list": [
                        {
                            "service": format_service_name(c.service),
                            "urgency": format_urgency(c.urgency),
                            "ordered": c.date_time.isoformat(),
                            "days_overdue": (datetime.now() - c.date_time).days,
                            "reason": c.reason,
                        }
                        for c in overdue_consults
                    ],
                    "all_consults": [
                        {
                            "id": c.local_id,
                            "service": format_service_name(c.service),
                            "status": format_status(c.status_name),
                            "urgency": format_urgency(c.urgency),
                            "ordered": c.date_time.isoformat(),
                            "scheduled": (
                                c.scheduled_date.isoformat()
                                if c.scheduled_date
                                else None
                            ),
                            "completed": (
                                c.completed_date.isoformat()
                                if c.completed_date
                                else None
                            ),
                            "provider": c.provider_name,
                            "reason": c.reason,
                            "overdue": c.is_overdue,
                        }
                        for c in consults
                    ],
                },
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
            logger.exception("Unexpected error in get_patient_consults")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
