"""Get patient vitals tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from ...models.patient import VitalSign
from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
    VitalsFiltersMetadata,
)
from ...models.responses.tool_responses import (
    VitalSignsResponse,
    VitalSignsResponseData,
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


def register_get_patient_vitals_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_vitals tool with the MCP server"""

    @mcp.tool()
    async def get_patient_vitals(
        patient_icn: str,
        station: str | None = None,
        vital_type: str | None = None,
        n_most_recent: Annotated[int | None, Field(default=3, ge=0)] = 3,
        days_back: Annotated[int, Field(default=30, ge=0)] = 30,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
        ctx: Context | None = None,
    ) -> VitalSignsResponse:
        """Get patient vital signs with latest values and history."""
        start_time = datetime.now(UTC)
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )

        # Validate ICN
        if not validate_icn(patient_icn):
            md = ResponseMetadata(
                request_id=f"req_{int(start_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=0,
                    start_time=start_time,
                    end_time=start_time,
                ),
                station=StationMetadata(station_number=station),
                demographics=DemographicsMetadata(patient_icn=patient_icn),
            )
            return VitalSignsResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Filter vitals
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
            vitals = [v for v in patient_data.vital_signs if v.observed >= cutoff_date]

            # Filter by type if specified
            if vital_type:
                vitals = [
                    v for v in vitals if v.type_name.upper() == vital_type.upper()
                ]

            # group by type and have at most n per type, then flatten out.
            # TODO: there are smarter ways to do this
            if n_most_recent:
                vitals_by_type: dict[str, list[VitalSign]] = {}
                for vital_sign in vitals:
                    vitals_list = vitals_by_type.setdefault(vital_sign.type_code, [])
                    if len(vitals_list) < n_most_recent:
                        vitals_list.append(vital_sign)

            vitals = [
                vital_sign
                for vitals_list in vitals_by_type.values()
                for vital_sign in vitals_list
            ]

            # Apply pagination
            vitals_page, total_vitals_after_filtering = paginate_list(
                vitals, offset, limit
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
                filters=VitalsFiltersMetadata(
                    vital_type=vital_type,
                    days_back=days_back,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_vitals_after_filtering,
                    returned=len(vitals_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_vitals",
                    patient_icn=patient_icn,
                ),
            )

            # Build response data
            data = VitalSignsResponseData(
                vital_signs=vitals_page,
            )

            return VitalSignsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.exception("Unexpected error in get_patient_vitals")
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
            return VitalSignsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
