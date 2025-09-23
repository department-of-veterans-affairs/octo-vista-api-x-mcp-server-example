"""Get patient problems tool for MCP server"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ProblemsFiltersMetadata,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import ProblemsResponse, ProblemsResponseData
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


def register_get_patient_problems_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_problems tool with the MCP server"""

    @mcp.tool()
    async def get_patient_problems(
        patient_icn: str,
        station: str | None = None,
        active_only: bool = True,
        service_connected_only: bool = False,
        verified_only: bool = False,
        unremoved_only: bool = False,
        days_back: Annotated[int, Field(default=365, ge=1, le=36500)] = 365,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
        ctx: Context | None = None,
    ) -> ProblemsResponse:
        """Get patient problem records with filtering and pagination."""
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
            return ProblemsResponse(
                success=False,
                error=f"Invalid patient ICN: {patient_icn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Extract problems from patient data
            problems = patient_data.problems

            # Filter problems by date range
            cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

            # Filter problems by date, active status, and service connection
            problems = [
                problem
                for problem in problems
                if problem.entered >= cutoff_date
                and (not active_only or problem.is_active)
                and (not service_connected_only or problem.is_service_connected)
                and (not verified_only or not problem.unverified)
                and (not unremoved_only or not problem.removed)
            ]

            # Apply pagination
            problems_page, total_filtered_problems = paginate_list(
                problems, offset, limit
            )

            # Group problems by status
            by_status = {"ACTIVE": 0, "INACTIVE": 0}
            active_problems = []
            inactive_problems = []

            for problem in problems_page:
                if problem.is_active:
                    by_status["ACTIVE"] += 1
                    active_problems.append(problem.uid)
                else:
                    by_status["INACTIVE"] += 1
                    inactive_problems.append(problem.uid)

            # Group by acuity
            by_acuity = {"CHRONIC": 0, "ACUTE": 0}
            for problem in problems_page:
                if problem.is_chronic:
                    by_acuity["CHRONIC"] += 1
                elif problem.is_acute:
                    by_acuity["ACUTE"] += 1

            # Get service connected problems
            service_connected_problems = [
                problem.uid for problem in problems_page if problem.is_service_connected
            ]

            # Calculate summary statistics
            facilities = list(
                {problem.facility_name for problem in problems if problem.facility_name}
            )
            services = list(
                {problem.service for problem in problems if problem.service}
            )
            icd_codes = list(
                {
                    problem.icd_code
                    for problem in problems
                    if problem.has_icd_code and problem.icd_code is not None
                }
            )

            from ...models.patient.problem import ProblemSummary

            summary = ProblemSummary(
                total_problems=total_filtered_problems,
                active_count=by_status["ACTIVE"],
                inactive_count=by_status["INACTIVE"],
                chronic_count=by_acuity["CHRONIC"],
                acute_count=by_acuity["ACUTE"],
                service_connected_count=len(service_connected_problems),
                date_range_days=days_back,
                most_recent_problem=problems[0].entered if problems else None,
                facilities=facilities,
                services=services,
                icd_codes=icd_codes,
            )

            # Build response data
            data = ProblemsResponseData(
                problems=problems_page,
                summary=summary,
                by_status=by_status,
                by_acuity=by_acuity,
                active_problems=active_problems,
                inactive_problems=inactive_problems,
                service_connected_problems=service_connected_problems,
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
                demographics=DemographicsMetadata.from_patient_demographics(
                    patient_data.demographics,
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_filtered_problems,
                    offset=offset,
                    limit=limit,
                    returned=len(problems_page),
                    tool_name="get_patient_problems",
                    patient_icn=patient_icn,
                ),
                filters=ProblemsFiltersMetadata(
                    days_back=days_back,
                    active_only=active_only,
                    service_connected_only=service_connected_only,
                ),
            )

            return ProblemsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"[DEBUG] Exception in get_patient_problems: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_problems")
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
            return ProblemsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
