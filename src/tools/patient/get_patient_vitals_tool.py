"""Get patient vitals tool for MCP server"""

import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.formatters import format_vital_type
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_vitals_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_vitals tool with the MCP server"""

    @mcp.tool()
    async def get_patient_vitals(
        patient_dfn: str,
        station: str | None = None,
        vital_type: str | None = None,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """Get patient vital signs with latest values and history."""
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

            # Filter vitals
            cutoff_date = datetime.now() - timedelta(days=days_back)
            vitals = [v for v in patient_data.vital_signs if v.observed >= cutoff_date]

            # Filter by type if specified
            if vital_type:
                vitals = [
                    v for v in vitals if v.type_name.upper() == vital_type.upper()
                ]

            # Get latest of each type
            latest_vitals = patient_data.get_latest_vitals()

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                    "age": patient_data.demographics.calculate_age(),
                },
                "vitals": {
                    "count": len(vitals),
                    "days_back": days_back,
                    "filtered_type": vital_type,
                    "latest": {
                        format_vital_type(type_name): {
                            "value": vital.display_value,
                            "date": vital.observed.isoformat(),
                            "abnormal": vital.is_abnormal,
                            "critical": vital.is_critical,
                        }
                        for type_name, vital in latest_vitals.items()
                    },
                    "history": [
                        {
                            "type": format_vital_type(v.type_name),
                            "value": v.display_value,
                            "date": v.observed.isoformat(),
                            "abnormal": v.is_abnormal,
                            "critical": v.is_critical,
                            "location": v.location_name,
                        }
                        for v in vitals
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
            logger.exception("Unexpected error in get_patient_vitals")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
