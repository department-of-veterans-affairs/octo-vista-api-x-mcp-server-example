"""Get patient treatments tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.patient.treatment import TreatmentStatusFilter
from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    TreatmentsResponse,
    TreatmentsResponseData,
)
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_treatments_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_treatments tool with the MCP server"""

    @mcp.tool()
    async def get_patient_treatments(
        patient_dfn: str,
        station: str | None = None,
        status_filter: TreatmentStatusFilter | None = None,
        complexity_filter: str | None = None,  # "low", "moderate", "high"
        specialty_filter: str | None = None,
        days_back: Annotated[int, Field(default=30, ge=1, le=3650)] = 30,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> TreatmentsResponse:
        """Get patient treatments with status, complexity, and outcome information."""
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
            return TreatmentsResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Get treatments from patient data
            treatments = patient_data.treatments

            # Apply patient_dfn filter to ensure only treatments for the requested patient
            treatments = [t for t in treatments if t.dfn == patient_dfn]

            # Apply days_back filter to scope treatments by date
            cutoff_date = start_time - timedelta(days=days_back)
            treatments = [t for t in treatments if t.date >= cutoff_date]

            # Apply filters
            if status_filter:
                if status_filter == TreatmentStatusFilter.ACTIVE:
                    treatments = [t for t in treatments if t.is_active]
                elif status_filter == TreatmentStatusFilter.COMPLETED:
                    treatments = [t for t in treatments if t.is_completed]
                elif status_filter == TreatmentStatusFilter.PLANNED:
                    treatments = [t for t in treatments if t.is_scheduled]

            if complexity_filter:
                treatments = [
                    t
                    for t in treatments
                    if t.complexity
                    and str(t.complexity).lower() == complexity_filter.lower()
                ]

            if specialty_filter:
                treatments = [
                    t
                    for t in treatments
                    if t.specialty and specialty_filter.upper() in t.specialty.upper()
                ]

            # Apply pagination
            treatments_page, total_treatments_after_filtering = paginate_list(
                treatments, offset, limit
            )

            # Build summary data using the full filtered treatments list (not just the page)
            # This gives users complete statistics across all matching results

            # Get UIDs directly with single comprehensions over full filtered results
            active_treatments_uids = [t.uid for t in treatments if t.is_active]
            completed_treatments_uids = [t.uid for t in treatments if t.is_completed]
            scheduled_treatments_uids = [t.uid for t in treatments if t.is_scheduled]

            # Group by status
            by_status: dict[str, int] = {}
            for treatment in treatments:
                status = str(treatment.status) if treatment.status else "unknown"
                by_status[status] = by_status.get(status, 0) + 1

            # Group by complexity
            by_complexity: dict[str, int] = {}
            for treatment in treatments:
                complexity = (
                    str(treatment.complexity) if treatment.complexity else "unknown"
                )
                by_complexity[complexity] = by_complexity.get(complexity, 0) + 1

            # Group by specialty
            by_specialty: dict[str, int] = {}
            for treatment in treatments:
                specialty = treatment.specialty or "unknown"
                by_specialty[specialty] = by_specialty.get(specialty, 0) + 1

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
                pagination=PaginationMetadata(
                    total_available_items=total_treatments_after_filtering,
                    returned=len(treatments_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_treatments",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = TreatmentsResponseData(
                treatments=treatments_page,
                active_treatments=sorted(active_treatments_uids),
                completed_treatments=sorted(completed_treatments_uids),
                scheduled_treatments=sorted(scheduled_treatments_uids),
                by_status=by_status,
                by_complexity=by_complexity,
                by_specialty=by_specialty,
            )

            return TreatmentsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"[DEBUG] Exception in get_patient_treatments: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_treatments")
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
            return TreatmentsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
