"""Get patient labs tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from ...models.patient import LabResult
from ...models.responses.metadata import (
    DemographicsMetadata,
    LabsFiltersMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    LabResultsResponse,
    LabResultsResponseData,
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


def register_get_patient_labs_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_labs tool with the MCP server"""

    @mcp.tool()
    async def get_patient_labs(
        patient_icn: str,
        station: str | None = None,
        abnormal_only: bool = False,
        lab_type: str | None = None,
        n_most_recent: Annotated[int | None, Field(default=3, ge=0)] = 3,
        days_back: Annotated[int, Field(default=90, ge=0)] = 90,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=200, ge=1, le=200)] = 200,
        ctx: Context | None = None,
    ) -> LabResultsResponse:
        """Get patient laboratory test results with values and reference ranges."""
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
            return LabResultsResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Filter labs with combined conditions
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
            labs = [
                lab
                for lab in patient_data.lab_results
                if lab.observed >= cutoff_date
                and (not abnormal_only or lab.is_abnormal)
                and (not lab_type or lab_type.upper() in lab.type_name.upper())
            ]

            # group by type and have at most n per type, then flatten out.
            # TODO: there are smarter ways to do this
            if n_most_recent:
                labs_by_type: dict[str, list[LabResult]] = {}
                for lab in labs:
                    lab_list = labs_by_type.setdefault(lab.type_code, [])
                    if len(lab_list) < n_most_recent:
                        lab_list.append(lab)

            labs = [lab for lab_list in labs_by_type.values() for lab in lab_list]

            # Apply pagination
            labs_page, total_filtered_labs = paginate_list(labs, offset, limit)

            # Group by test type (for paginated results)
            lab_groups: dict[str, list[Any]] = {}
            for lab in labs_page:
                if lab.type_code not in lab_groups:
                    lab_groups[lab.type_code] = []
                lab_groups[lab.type_code].append(lab.uid)

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
                filters=LabsFiltersMetadata(
                    abnormal_only=abnormal_only,
                    lab_type=lab_type,
                    days_back=days_back,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_filtered_labs,
                    offset=offset,
                    limit=limit,
                    returned=len(labs_page),
                    tool_name="get_patient_labs",
                    patient_icn=patient_icn,
                ),
            )

            # Build response data
            data = LabResultsResponseData(
                abnormal_count=len([lab for lab in labs_page if lab.is_abnormal]),
                critical_count=len([lab for lab in labs_page if lab.is_critical]),
                labs=labs_page,
            )

            return LabResultsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.exception("Unexpected error in get_patient_labs")
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
            return LabResultsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
