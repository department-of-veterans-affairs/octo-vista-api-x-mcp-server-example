"""Get patient health factors tool for MCP server"""

from datetime import UTC, datetime
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    HealthFactorsFiltersMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    HealthFactorsResponse,
    HealthFactorsResponseData,
)
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import (
    get_default_duz,
    get_default_station,
    get_logger,
    paginate_list,
    resolve_vista_context,
)
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_health_factors_tool(
    mcp: FastMCP, vista_client: BaseVistaClient
):
    """Register the get_patient_health_factors tool with the MCP server"""

    @mcp.tool()
    async def get_patient_health_factors(
        patient_icn: str,
        station: str | None = None,
        category_filter: str | None = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
        ctx: Context | None = None,
    ) -> HealthFactorsResponse:
        """Get patient health factors."""
        start_time = datetime.now(UTC)
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )

        # Validate ICN
        if not validate_icn(patient_icn):
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
            return HealthFactorsResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Filter health factors by category if specified
            health_factors = [
                f
                for f in patient_data.health_factors
                if not category_filter or category_filter.upper() in f.category.upper()
            ]

            # Apply pagination
            health_factors_page, total_health_factors_after_filtering = paginate_list(
                health_factors, offset, limit
            )

            # Build typed metadata inline
            end_time = datetime.now(UTC)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            rpc_details = RpcCallMetadata(
                rpc="VPR GET PATIENT DATA JSON",
                context="LHS RPC CONTEXT",
                parameters=build_icn_only_named_array_param(patient_icn),
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
                demographics=DemographicsMetadata.from_patient_demographics(
                    patient_data.demographics,
                ),
                filters=HealthFactorsFiltersMetadata(
                    category_filter=category_filter,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_health_factors_after_filtering,
                    returned=len(health_factors_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_health_factors",
                    patient_icn=patient_icn,
                ),
            )

            # Build response data
            data = HealthFactorsResponseData(
                health_factors=health_factors_page,
            )

            return HealthFactorsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"[DEBUG] Exception in get_patient_health_factors: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_health_factors")
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
            return HealthFactorsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
