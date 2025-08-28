"""Patient visit MCP tool"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.patient.base import FacilityInfo
from ...models.patient.visits import VisitSummary
from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
    VisitsFiltersMetadata,
)
from ...models.responses.tool_responses import VisitsResponse, VisitsResponseData
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


async def get_patient_visits(
    patient_dfn: str,
    vista_client: BaseVistaClient,
    station: str | None = None,
    visit_type: str = "",
    active_only: bool = False,
    days_back: int = 365,
    offset: int = 0,
    limit: int = 10,
) -> VisitsResponse:
    """Get patient visit history with location and duration data."""
    start_time = datetime.now(UTC)
    station = station or get_default_station()
    caller_duz = get_default_duz()

    logger.info(
        f"🏥 [DEBUG] get_patient_visits: patient_dfn={patient_dfn}, station={station}, visit_type={visit_type}, active_only={active_only}, days_back={days_back}, offset={offset}, limit={limit}"
    )

    # Validate DFN
    if not validate_dfn(patient_dfn):
        end_time = datetime.now(UTC)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        return VisitsResponse(
            success=False,
            error="Invalid patient DFN format. DFN must be numeric.",
            data=VisitsResponseData(
                patient_dfn=patient_dfn, summary=VisitSummary(total_visits=0)
            ),
            metadata=ResponseMetadata(
                request_id=f"visits_{patient_dfn}_{int(start_time.timestamp())}",
                station=StationMetadata(station_number=station),
                performance=PerformanceMetrics(
                    duration_ms=duration_ms, start_time=start_time, end_time=end_time
                ),
            ),
        )

    # Validate days_back parameter
    if days_back < 1 or days_back > 1095:
        end_time = datetime.now(UTC)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        return VisitsResponse(
            success=False,
            error="Days back must be between 1 and 1095",
            data=VisitsResponseData(
                patient_dfn=patient_dfn, summary=VisitSummary(total_visits=0)
            ),
            metadata=ResponseMetadata(
                request_id=f"visits_{patient_dfn}_{int(start_time.timestamp())}",
                station=StationMetadata(station_number=station),
                performance=PerformanceMetrics(
                    duration_ms=duration_ms, start_time=start_time, end_time=end_time
                ),
            ),
        )

    try:
        # Get patient data (handles caching internally)
        patient_data = await get_patient_data(
            vista_client,
            station,
            patient_dfn,
            caller_duz,
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
            visits = [
                v for v in visits if v.status_code and v.status_code.lower() == "active"
            ]

        # Filter by date range
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
        visits = [v for v in visits if v.visit_date and v.visit_date >= cutoff_date]

        # Apply pagination
        visits_page, total_visits_after_filtering = paginate_list(visits, offset, limit)

        # Use the paginated visits for the response
        visit_summaries = visits_page

        # Calculate end time and duration
        end_time = datetime.now(UTC)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Build visits summary with actual data from visits
        # Extract unique visit types from visits
        unique_visit_types = list(
            {visit.visit_type for visit in visits if visit.visit_type}
        )

        # Extract unique facilities from visits
        unique_facilities = {}
        for visit in visits:
            if visit.facility_code and visit.facility_name:
                unique_facilities[visit.facility_code] = visit.facility_name

        facility_infos = [
            FacilityInfo(code=str(code), name=name)
            for code, name in unique_facilities.items()
        ]

        visits_summary = VisitSummary(
            total_visits=total_visits_after_filtering,
            last_visit=visits[0].visit_date if visits else None,
            visit_types=unique_visit_types,
            facilities=facility_infos,
        )

        # Build response data
        response_data = VisitsResponseData(
            patient_dfn=patient_dfn,
            patient_name=patient_data.patient_name,
            patient_age=(
                patient_data.demographics.calculate_age()
                if hasattr(patient_data.demographics, "calculate_age")
                else None
            ),
            patient_gender=(
                patient_data.demographics.gender_name
                if hasattr(patient_data.demographics, "gender_name")
                else None
            ),
            summary=visits_summary,
            all_visits=visit_summaries,
            filters={
                "visit_type": visit_type,
                "active_only": active_only,
                "days_back": days_back,
            },
        )

        # Build metadata
        metadata = ResponseMetadata(
            request_id=f"visits_{patient_dfn}_{int(start_time.timestamp())}",
            station=StationMetadata(station_number=station),
            performance=PerformanceMetrics(
                duration_ms=duration_ms, start_time=start_time, end_time=end_time
            ),
            rpc=RpcCallMetadata(
                rpc="VPR GET PATIENT DATA JSON",
                context="LHS RPC CONTEXT",
                parameters=[{"namedArray": {"patientId": patient_dfn}}],
                duz=caller_duz,
            ),
            demographics=DemographicsMetadata(
                patient_dfn=patient_dfn,
                patient_name=patient_data.patient_name,
            ),
            filters=VisitsFiltersMetadata(
                visit_type=visit_type,
                active_only=active_only,
                days_back=days_back,
            ),
            pagination=PaginationMetadata(
                total_available_items=total_visits_after_filtering,
                returned=len(visits_page),
                offset=offset,
                limit=limit,
                tool_name="get_patient_visits",
                patient_dfn=patient_dfn,
            ),
        )

        # Build final response
        return VisitsResponse(success=True, data=response_data, metadata=metadata)

    except Exception as e:
        logger.exception("Unexpected error in get_patient_visits")
        end_time = datetime.now(UTC)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return VisitsResponse(
            success=False,
            error=f"Unexpected error: {str(e)}",
            data=VisitsResponseData(
                patient_dfn=patient_dfn, summary=VisitSummary(total_visits=0)
            ),
            metadata=ResponseMetadata(
                request_id=f"visits_{patient_dfn}_{int(start_time.timestamp())}",
                station=StationMetadata(station_number=station),
                performance=PerformanceMetrics(
                    duration_ms=duration_ms, start_time=start_time, end_time=end_time
                ),
            ),
        )


def register_get_patient_visits_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_visits tool with the MCP server"""

    @mcp.tool()
    async def get_patient_visits_tool(
        patient_dfn: str,
        station: str | None = None,
        visit_type: str = "",
        active_only: bool = False,
        days_back: Annotated[int, Field(default=365, ge=1)] = 365,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> VisitsResponse:
        """Get patient visit history with location and duration data."""
        return await get_patient_visits(
            patient_dfn=patient_dfn,
            station=station,
            visit_type=visit_type,
            active_only=active_only,
            days_back=days_back,
            offset=offset,
            limit=limit,
            vista_client=vista_client,
        )
