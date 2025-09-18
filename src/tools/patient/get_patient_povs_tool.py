"""Get patient POVs (Purpose of Visit) tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.patient.pov import POVSummary
from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    POVsFiltersMetadata,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import POVsResponse, POVsResponseData
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_povs_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_povs tool with the MCP server"""

    @mcp.tool()
    async def get_patient_povs(
        patient_icn: str,
        station: str | None = None,
        primary_only: bool = False,
        days_back: Annotated[int, Field(default=365, ge=1, le=1095)] = 365,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> POVsResponse:
        """Get patient Purpose of Visit (POV) records with filtering and pagination."""
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
            return POVsResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Extract POVs from patient data
            povs = patient_data.povs

            # Filter POVs by date range
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

            # Filter POVs by date and primary status
            povs = [
                pov
                for pov in povs
                if pov.entered >= cutoff_date and (not primary_only or pov.is_primary)
            ]

            # Apply pagination
            povs_page, total_filtered_povs = paginate_list(povs, offset, limit)

            # Group POVs by encounter
            by_encounter: dict[str, list[str]] = {}
            for pov in povs_page:
                encounter_uid = pov.encounter_uid
                if encounter_uid not in by_encounter:
                    by_encounter[encounter_uid] = []
                by_encounter[encounter_uid].append(pov.uid)

            # Group by type
            by_type = {"Primary": 0, "Secondary": 0}
            primary_povs = []
            secondary_povs = []

            for pov in povs_page:
                if pov.is_primary:
                    by_type["Primary"] += 1
                    primary_povs.append(pov.uid)
                else:
                    by_type["Secondary"] += 1
                    secondary_povs.append(pov.uid)

            # Calculate summary statistics
            unique_encounters = len({pov.encounter_uid for pov in povs})
            facilities = list({pov.facility_name for pov in povs if pov.facility_name})
            encounter_types = list(
                {pov.encounter_name for pov in povs if pov.encounter_name}
            )

            summary = POVSummary(
                total_povs=total_filtered_povs,
                primary_count=by_type["Primary"],
                secondary_count=by_type["Secondary"],
                unique_encounters=unique_encounters,
                date_range_days=days_back,
                most_recent_pov=povs[0].entered if povs else None,
                facilities=facilities,
                encounter_types=encounter_types,
            )

            # Build response data
            data = POVsResponseData(
                povs=povs_page,
                summary=summary,
                by_encounter=by_encounter,
                by_type=by_type,
                primary_povs=primary_povs,
                secondary_povs=secondary_povs,
            )

            # Build metadata
            end_time = datetime.now(UTC)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            md = ResponseMetadata(
                request_id=f"req_{int(end_time.timestamp())}",
                performance=PerformanceMetrics(
                    duration_ms=duration_ms,
                    start_time=start_time,
                    end_time=end_time,
                ),
                station=StationMetadata(station_number=station),
                rpc=RpcCallMetadata(
                    rpc="VPR GET PATIENT DATA JSON",
                    context="LHS RPC CONTEXT",
                    parameters=build_icn_only_named_array_param(patient_icn),
                    duz=caller_duz,
                ),
                demographics=DemographicsMetadata(
                    patient_icn=patient_icn,
                    patient_name=patient_data.patient_name,
                    patient_age=patient_data.demographics.calculate_age(),
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_filtered_povs,
                    offset=offset,
                    limit=limit,
                    returned=len(povs_page),
                    tool_name="get_patient_povs",
                    patient_icn=patient_icn,
                ),
                filters=POVsFiltersMetadata(
                    days_back=days_back,
                    primary_only=primary_only,
                ),
            )

            return POVsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"[DEBUG] Exception in get_patient_povs: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_povs")
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
            return POVsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
