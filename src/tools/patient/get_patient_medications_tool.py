"""Get patient medications tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    MedicationsFiltersMetadata,
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
        active_only: bool = False,
        return_all_active_and_pending: bool = True,  # returns active/pending regardless of cutoff date
        days_back: Annotated[int, Field(default=183, ge=1, le=36500)] = 183,  # 6 months
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=100, ge=1, le=1000)] = 100,
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

            # Filter medications based on active status and days back
            cutoff_date = (
                datetime.now(UTC) - timedelta(days=days_back) if days_back else None
            )
            medications = [
                m
                for m in patient_data.medications
                if (return_all_active_and_pending and (m.is_pending or m.is_active))
                or (
                    (not active_only or m.is_active)
                    and (
                        cutoff_date is None
                        or (m.last_filled and m.last_filled >= cutoff_date)
                    )
                )
            ]

            # Apply pagination
            medications_page, total_medications_after_filtering = paginate_list(
                medications, offset, limit
            )

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
                filters=MedicationsFiltersMetadata(
                    active_only=active_only,
                ),
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
            )

            return MedicationsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"[DEBUG] Exception in get_patient_medications: {type(e).__name__}: {str(e)}"
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
