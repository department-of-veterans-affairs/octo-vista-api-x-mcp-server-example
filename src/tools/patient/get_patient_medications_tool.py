"""Get patient medications tool for MCP server"""

from datetime import UTC, datetime
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    MedicationsResponse,
    MedicationsResponseData,
)
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_medications_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_medications tool with the MCP server"""

    @mcp.tool()
    async def get_patient_medications(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
        therapeutic_class: str | None = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> MedicationsResponse:
        """Get patient medications with dosing and refill information."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            end_time = datetime.now(UTC)
            md = ResponseMetadata(
                request_id=f"req_{int(start_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=int((end_time - start_time).total_seconds() * 1000),
                    start_time=start_time,
                    end_time=end_time,
                ),
                station=StationMetadata(station_number=station),
            )
            return MedicationsResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter medications
            medications = patient_data.medications
            if active_only:
                medications = [m for m in medications if m.is_active]

            # Filter by therapeutic class
            if therapeutic_class:
                medications = [
                    m
                    for m in medications
                    if (
                        m.therapeutic_class
                        and therapeutic_class.upper() in m.therapeutic_class.upper()
                    )
                    or (m.va_class and therapeutic_class.upper() in m.va_class.upper())
                ]

            # Apply pagination
            medications_page, total_medications_after_filtering = paginate_list(
                medications, offset, limit
            )

            # Group medications by therapeutic class for better organization
            medication_groups: dict[str, list[Any]] = {}
            for med in medications_page:
                group_key = med.therapeutic_class or med.va_class or "Other"
                if group_key not in medication_groups:
                    medication_groups[group_key] = []
                medication_groups[group_key].append(med)

            # Identify medications needing refills soon (from paginated results)
            refill_alerts = [m for m in medications_page if m.needs_refill_soon]

            # Build typed metadata inline
            end_time = datetime.now(UTC)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            rpc_details = RpcCallMetadata(
                rpc="VPR GET PATIENT DATA JSON",
                context="LHS RPC CONTEXT",
                parameters=[{"namedArray": {"patientId": patient_dfn}}],
                duz=caller_duz,
            )
            md = ResponseMetadata(
                request_id=f"req_{int(end_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=duration_ms,
                    start_time=start_time,
                    end_time=end_time,
                ),
                station=StationMetadata(station_number=station),
                rpc=rpc_details,
                demographics=DemographicsMetadata(
                    patient_dfn=patient_dfn,
                    patient_name=patient_data.patient_name,
                    patient_age=patient_data.demographics.calculate_age(),
                ),
                additional_info={
                    "active_only_filter": active_only,
                    "therapeutic_class_filter": therapeutic_class,
                },
                pagination=PaginationMetadata(
                    total_available_items=total_medications_after_filtering,
                    returned=len(medications_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_medications",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = MedicationsResponseData(
                medications=medications_page,
                refill_alerts=refill_alerts,
            )

            return MedicationsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"🩺 [DEBUG] Exception in get_patient_medications: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_medications")
            end_time = datetime.now(UTC)
            md = ResponseMetadata(
                request_id=f"req_{int(end_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=int((end_time - start_time).total_seconds() * 1000),
                    start_time=start_time,
                    end_time=end_time,
                ),
                station=StationMetadata(station_number=station),
            )
            return MedicationsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
