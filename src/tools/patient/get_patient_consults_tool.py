"""Get patient consults tool for MCP server"""

from datetime import UTC, datetime
from typing import Annotated

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
    ConsultsResponse,
    ConsultsResponseData,
)
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_consults_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_consults tool with the MCP server"""

    @mcp.tool()
    async def get_patient_consults(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> ConsultsResponse:
        """Get patient consultation requests and referrals."""
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
            return ConsultsResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter consults
            consults = patient_data.consults
            if active_only:
                consults = [c for c in consults if c.is_active]

            # Apply pagination
            consults_page, total_consults_after_filtering = paginate_list(
                consults, offset, limit
            )

            # Get overdue consults
            overdue_consults = [c for c in consults_page if c.is_overdue]

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
                },
                pagination=PaginationMetadata(
                    total_available_items=total_consults_after_filtering,
                    returned=len(consults_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_consults",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = ConsultsResponseData(
                overdue_list=[c.uid for c in overdue_consults],
                consults=consults_page,
            )

            return ConsultsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.exception("Unexpected error in get_patient_consults")
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
            return ConsultsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
