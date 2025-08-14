"""Get patient labs tool for MCP server"""

from datetime import UTC, datetime, timedelta
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
    LabResultsResponse,
    LabResultsResponseData,
)
from ...services.data import get_patient_data
from ...services.formatters import format_lab_type
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
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
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> LabResultsResponse:
        """Get patient laboratory test results with values and reference ranges."""
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
            return LabResultsResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
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

            # Apply pagination
            labs_page, total_filtered_labs = paginate_list(labs, offset, limit)

            # Group by test type (for paginated results)
            lab_groups: dict[str, list[Any]] = {}
            for lab in labs_page:
                if lab.type_name not in lab_groups:
                    lab_groups[lab.type_name] = []
                lab_groups[lab.type_name].append(lab.uid)

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
                    "abnormal_only_filter": abnormal_only,
                    "lab_type_filter": lab_type,
                    "days_back_filter": days_back,
                },
                pagination=PaginationMetadata(
                    total_available_items=total_filtered_labs,
                    offset=offset,
                    limit=limit,
                    returned=len(labs_page),
                    tool_name="get_patient_labs",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = LabResultsResponseData(
                abnormal_count=len([lab for lab in labs_page if lab.is_abnormal]),
                critical_count=len([lab for lab in labs_page if lab.is_critical]),
                days_back=days_back,
                by_type={
                    format_lab_type(test_type): results
                    for test_type, results in lab_groups.items()
                },
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
