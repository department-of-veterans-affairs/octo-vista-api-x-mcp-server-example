"""Get patient vitals tool for MCP server"""

from datetime import UTC, datetime, timedelta
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
    VitalSignsResponse,
    VitalSignsResponseData,
)
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_vitals_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_vitals tool with the MCP server"""

    @mcp.tool()
    async def get_patient_vitals(
        patient_dfn: str,
        station: str | None = None,
        vital_type: str | None = None,
        days_back: int = 30,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> VitalSignsResponse:
        """Get patient vital signs with latest values and history."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            md = ResponseMetadata(
                request_id=f"req_{int(start_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=0,
                    start_time=start_time,
                    end_time=start_time,
                ),
                station=StationMetadata(station_number=station),
                demographics=DemographicsMetadata(patient_dfn=patient_dfn),
            )
            return VitalSignsResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter vitals
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
            vitals = [v for v in patient_data.vital_signs if v.observed >= cutoff_date]

            # Filter by type if specified
            if vital_type:
                vitals = [
                    v for v in vitals if v.type_name.upper() == vital_type.upper()
                ]

            # Apply pagination
            vitals_page, total_vitals_after_filtering = paginate_list(
                vitals, offset, limit
            )

            # Get latest of each type
            latest_vitals = patient_data.get_latest_vitals()

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
                    "vital_type_filter": vital_type,
                    "days_back_filter": days_back,
                },
                pagination=PaginationMetadata(
                    total_available_items=total_vitals_after_filtering,
                    returned=len(vitals_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_vitals",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = VitalSignsResponseData(
                vital_signs=vitals_page,
                latest_vitals=latest_vitals,
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
