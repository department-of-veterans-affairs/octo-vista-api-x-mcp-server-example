"""Patient visit MCP tool"""

import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


async def get_patient_visits(
    patient_dfn: str,
    station: str | None = None,
    visit_type: str = "",
    active_only: bool = False,
    days_back: int = 365,
    vista_client: BaseVistaClient | None = None,
) -> dict[str, Any]:
    """Get patient visit history with location and duration data."""
    start_time = time.time()
    station = station or get_default_station()
    caller_duz = get_default_duz()

    logger.info(
        f"🏥 [DEBUG] get_patient_visits: patient_dfn={patient_dfn}, station={station}, visit_type={visit_type}, active_only={active_only}, days_back={days_back}"
    )

    # Validate DFN
    if not validate_dfn(patient_dfn):
        return {
            "success": False,
            "error": "Invalid patient DFN format. DFN must be numeric.",
            "metadata": build_metadata(station=station),
        }

    # Validate days_back parameter
    if days_back < 1 or days_back > 1095:
        return {
            "success": False,
            "error": "Days back must be between 1 and 1095",
            "metadata": build_metadata(station=station),
        }

    try:
        # Get patient data (handles caching internally)
        patient_data = await get_patient_data(
            vista_client, station, patient_dfn, caller_duz  # type: ignore
        )

        # Filter visits
        visits = patient_data.visits

        # Filter by visit type
        if visit_type:
            visits = [
                v
                for v in visits
                if (
                    hasattr(v.visit_type, "value")
                    and v.visit_type.value.lower() == visit_type.lower()
                )
                or (
                    isinstance(v.visit_type, str)
                    and v.visit_type.lower() == visit_type.lower()
                )
            ]

        # Filter by active status
        if active_only:
            visits = [v for v in visits if v.is_active]

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days_back)
        visits = [v for v in visits if v.visit_date >= cutoff_date]

        # Group visits by type for summary
        visits_by_type: dict[str, list[Any]] = {}
        for visit in visits:
            visit_type_key = (
                visit.visit_type.value
                if hasattr(visit.visit_type, "value")
                else str(visit.visit_type)
            )
            if visit_type_key not in visits_by_type:
                visits_by_type[visit_type_key] = []
            visits_by_type[visit_type_key].append(visit)

        # Calculate summary statistics
        total_count = len(visits)
        active_count = len([v for v in visits if v.is_active])
        inpatient_count = len([v for v in visits if v.is_inpatient])
        emergency_count = len([v for v in visits if v.is_emergency])

        # Calculate average inpatient duration
        inpatient_visits = [
            v for v in visits if v.is_inpatient and v.duration_days is not None
        ]
        average_inpatient_duration_days = (
            sum(v.duration_days for v in inpatient_visits) / len(inpatient_visits)  # type: ignore
            if inpatient_visits
            else None
        )

        # Build visit summaries
        visit_summaries = []
        for visit in visits:
            summary = {
                "id": visit.uid,
                "visit_date": visit.visit_date.isoformat(),
                "location": visit.display_location,
                "standardized_location": visit.standardized_location_name,
                "location_summary": visit.location_summary,
                "provider": visit.provider_name,
                "status": visit.status_name,
                "visit_type": (
                    visit.visit_type.value
                    if hasattr(visit.visit_type, "value")
                    else str(visit.visit_type)
                ),
                "duration_days": visit.duration_days,
                "active": visit.is_active,
                "inpatient": visit.is_inpatient,
                "emergency": visit.is_emergency,
                "chief_complaint": visit.chief_complaint,
                "diagnosis": visit.diagnosis,
                "discharge_diagnosis": visit.discharge_diagnosis,
                "orders_count": len(visit.order_uids),
                "treatments_count": len(visit.treatment_uids),
            }
            visit_summaries.append(summary)

        # Build response with enhanced metadata
        metadata = build_metadata(
            station=station,
            duration_ms=int((time.time() - start_time) * 1000),
        )

        # Add filters metadata that tests expect
        metadata["filters"] = {
            "visit_type": visit_type,
            "active_only": active_only,
            "days_back": days_back,
        }

        # Add RPC metadata that tests expect
        metadata["rpc"] = {
            "rpc": "VPR GET PATIENT DATA JSON",
            "context": "LHS RPC CONTEXT",
            "jsonResult": True,
            "parameters": [{"namedArray": {"patientId": patient_dfn}}],
        }
        metadata["duz"] = caller_duz

        # Build response
        return {
            "success": True,
            "patient": {
                "dfn": patient_dfn,
                "name": patient_data.patient_name,
                "age": (
                    patient_data.demographics.calculate_age()
                    if hasattr(patient_data.demographics, "calculate_age")
                    else None
                ),
                "gender": (
                    patient_data.demographics.gender_name
                    if hasattr(patient_data.demographics, "gender_name")
                    else None
                ),
            },
            "visits": {
                "summary": {
                    "total_count": total_count,
                    "active_count": active_count,
                    "inpatient_count": inpatient_count,
                    "emergency_count": emergency_count,
                    "average_inpatient_duration_days": average_inpatient_duration_days,
                    "by_type": {
                        visit_type: len(visits_list)
                        for visit_type, visits_list in visits_by_type.items()
                    },
                },
                "all_visits": visit_summaries,
            },
            "metadata": metadata,
        }

    except Exception as e:
        logger.exception("Unexpected error in get_patient_visits")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "metadata": build_metadata(station=station),
        }


def register_get_patient_visits_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_visits tool with the MCP server"""

    @mcp.tool()
    async def get_patient_visits_tool(
        patient_dfn: str,
        station: str | None = None,
        visit_type: str = "",
        active_only: bool = False,
        days_back: int = 365,
    ) -> dict[str, Any]:
        """Get patient visit history with location and duration data."""
        return await get_patient_visits(
            patient_dfn=patient_dfn,
            station=station,
            visit_type=visit_type,
            active_only=active_only,
            days_back=days_back,
            vista_client=vista_client,
        )
