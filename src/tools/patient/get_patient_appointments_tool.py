"""Get patient appointments tool for MCP server"""

from datetime import UTC, datetime, timedelta
from functools import reduce
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    AppointmentsFiltersMetadata,
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    AppointmentsResponse,
    AppointmentsResponseData,
)
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_appointments_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_appointments tool with the MCP server"""

    @mcp.tool()
    async def get_patient_appointments(
        patient_icn: str,
        station: str | None = None,
        days_back: Annotated[int, Field(default=30, ge=0, le=3650)] = 30,
        status_filter: str | None = None,
        clinic_filter: str | None = None,
        category: str | None = None,
        provider_filter: str | None = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> AppointmentsResponse:
        """Get patient appointments and schedules."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()
        caller_duz = get_default_duz()

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
            return AppointmentsResponse(
                success=False,
                error="Invalid patient ICN format.",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Filter appointments by all criteria in a single pass
            now = datetime.now(UTC)
            past_cutoff = now - timedelta(days=days_back)
            status_upper = status_filter.upper() if status_filter else None
            clinic_upper = clinic_filter.upper() if clinic_filter else None
            category_upper = str(category).upper() if category else None
            provider_upper = provider_filter.upper() if provider_filter else None

            appointments = [
                apt
                for apt in patient_data.appointments
                if apt.appointment_date >= past_cutoff
                and (not status_upper or str(apt.status).upper() == status_upper)
                and (not clinic_upper or clinic_upper in apt.facility.name.upper())
                and (
                    not category_upper
                    or (
                        apt.category
                        and apt.category.type
                        and category_upper in str(apt.category.type).upper()
                    )
                )
                and (
                    not provider_upper
                    or any(
                        provider_upper in provider.provider_name.upper()
                        for provider in apt.providers
                    )
                )
            ]

            # Apply pagination
            appointments_page, total_appointments_after_filtering = paginate_list(
                appointments, offset, limit
            )

            # Split appointments into upcoming (next 7 days) and past
            future_appointments: list[str] = []
            past_appointments: list[str] = []
            future_appointments, past_appointments = reduce(
                lambda acc, apt: (
                    (acc[0].append(apt.uid) or acc)  # type: ignore[func-returns-value]
                    if apt.appointment_date > now
                    else (acc[1].append(apt.uid) or acc)  # type: ignore[func-returns-value]
                ),
                appointments_page,
                (future_appointments, past_appointments),
            )

            # Count by status
            by_status: dict[str, int] = {}
            for apt in appointments_page:
                status = str(apt.status)
                by_status[status] = by_status.get(status, 0) + 1

            # Count by clinic
            by_clinic: dict[str, int] = {}
            for apt in appointments_page:
                clinic = apt.facility.name
                by_clinic[clinic] = by_clinic.get(clinic, 0) + 1

            # Build metadata
            end_time = now
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
                filters=AppointmentsFiltersMetadata(
                    days_back=days_back,
                    status_filter=status_filter,
                    clinic_filter=clinic_filter,
                    appointment_type=str(category) if category else None,
                    provider_filter=provider_filter,
                    upcoming_only=days_back == 0,
                    past_only=False,  # Always includes future appointments
                ),
                pagination=PaginationMetadata(
                    total_available_items=total_appointments_after_filtering,
                    returned=len(appointments_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_appointments",
                    patient_icn=patient_icn,
                ),
            )

            # Build response data
            data = AppointmentsResponseData(
                future_count=len(future_appointments),
                past_count=len(past_appointments),
                by_status=by_status,
                by_clinic=by_clinic,
                appointments=appointments_page,
            )

            return AppointmentsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.exception("Unexpected error in get_patient_appointments")
            logger.error(f"Detailed error: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")

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
            return AppointmentsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
