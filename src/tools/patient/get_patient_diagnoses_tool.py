"""Get patient diagnoses tool for MCP server"""

from datetime import UTC, datetime
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    DiagnosesFiltersMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    DiagnosesResponse,
    DiagnosesResponseData,
)
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_diagnoses_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_diagnoses tool with the MCP server"""

    @mcp.tool()
    async def get_patient_diagnoses(
        patient_icn: str,
        station: str | None = None,
        status_filter: str | None = None,
        icd_version: str | None = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> DiagnosesResponse:
        """Get patient diagnoses with ICD codes."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()
        caller_duz = get_default_duz()

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
            return DiagnosesResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        # Validate limit parameter
        if limit < 1 or limit > 200:
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
            return DiagnosesResponse(
                success=False,
                error="Limit must be between 1 and 200.",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Apply pagination
            filtered_diagnoses_page, total_filtered_diagnoses = paginate_list(
                patient_data.diagnoses, offset, limit
            )

            # Get active diagnoses
            active_diagnoses = [
                d.uid for d in filtered_diagnoses_page if d.status.lower() == "active"
            ]

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
                demographics=DemographicsMetadata(
                    patient_icn=patient_icn,
                    patient_name=patient_data.patient_name,
                    patient_age=patient_data.demographics.calculate_age(),
                    patient_gender=patient_data.demographics.gender_name,
                ),
                filters=DiagnosesFiltersMetadata(
                    status_filter=status_filter,
                    icd_version=icd_version,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_filtered_diagnoses,
                    offset=offset,
                    limit=limit,
                    returned=len(filtered_diagnoses_page),
                    tool_name="get_patient_diagnoses",
                    patient_icn=patient_icn,
                ),
            )

            # Build response data
            data = DiagnosesResponseData(
                active_count=len(active_diagnoses),
                diagnoses=filtered_diagnoses_page,
            )

            return DiagnosesResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"[DEBUG] Exception in get_patient_diagnoses: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_diagnoses")
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
            return DiagnosesResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
