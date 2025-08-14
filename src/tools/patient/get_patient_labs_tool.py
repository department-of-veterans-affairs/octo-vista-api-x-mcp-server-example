"""Get patient labs tool for MCP server"""

import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.formatters import format_lab_type
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_labs_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_labs tool with the MCP server"""

    @mcp.tool()
    async def get_patient_labs(
        patient_dfn: str,
        station: str | None = None,
        abnormal_only: bool = False,
        lab_type: str | None = None,
        days_back: int = 90,
    ) -> dict[str, Any]:
        """Get patient laboratory test results with values and reference ranges."""
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

            # Filter labs
            cutoff_date = datetime.now() - timedelta(days=days_back)
            labs = [
                lab for lab in patient_data.lab_results if lab.observed >= cutoff_date
            ]

            # Filter by abnormal status
            if abnormal_only:
                labs = [lab for lab in labs if lab.is_abnormal]

            # Filter by type
            if lab_type:
                labs = [
                    lab for lab in labs if lab_type.upper() in lab.type_name.upper()
                ]

            # Group by test type
            lab_groups: dict[str, list[Any]] = {}
            for lab in labs:
                if lab.type_name not in lab_groups:
                    lab_groups[lab.type_name] = []
                lab_groups[lab.type_name].append(lab)

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                    "age": patient_data.demographics.calculate_age(),
                },
                "labs": {
                    "count": len(labs),
                    "abnormal_count": len([lab for lab in labs if lab.is_abnormal]),
                    "critical_count": len([lab for lab in labs if lab.is_critical]),
                    "days_back": days_back,
                    "filters": {
                        "abnormal_only": abnormal_only,
                        "lab_type": lab_type,
                    },
                    "by_type": {
                        format_lab_type(test_type): {
                            "count": len(results),
                            "latest": {
                                "value": results[0].display_value,
                                "date": results[0].observed.isoformat(),
                                "abnormal": results[0].is_abnormal,
                                "critical": results[0].is_critical,
                                "reference_range": (
                                    f"{results[0].low} - {results[0].high}"
                                    if results[0].low and results[0].high
                                    else None
                                ),
                            },
                            "trend": [
                                {
                                    "value": r.result,
                                    "numeric": r.numeric_result,
                                    "date": r.observed.isoformat(),
                                    "abnormal": r.is_abnormal,
                                }
                                for r in results[:5]  # Last 5 results
                            ],
                        }
                        for test_type, results in lab_groups.items()
                    },
                    "all_results": [
                        {
                            "test": lab.type_name,
                            "value": lab.display_value,
                            "date": lab.observed.isoformat(),
                            "abnormal": lab.is_abnormal,
                            "critical": lab.is_critical,
                            "interpretation": lab.interpretation_name,
                            "specimen": lab.specimen,
                            "group": lab.group_name,
                        }
                        for lab in labs[:100]  # Limit to 100 results
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
            logger.exception("Unexpected error in get_patient_labs")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
