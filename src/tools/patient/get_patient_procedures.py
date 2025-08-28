"""Get patient procedures tool - retrieve CPT codes and procedure data"""

from datetime import UTC, date, datetime
from typing import Annotated, Any

from pydantic import Field

from ...models.patient.cpt_code import CPTCode
from ...models.responses.metadata import (
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ProceduresFiltersMetadata,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    ProceduresResponse,
    ProceduresResponseData,
)
from ...services.data.patient_data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient, VistaAPIError

logger = get_logger(__name__)


async def get_patient_procedures_impl(
    vista_client: BaseVistaClient,
    patient_dfn: str,
    station: str | None = None,
    caller_duz: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: int = 0,
    limit: int = 50,
) -> ProceduresResponse:
    """
    Implementation for getting patient procedures/CPT codes

    Args:
        vista_client: Vista API client
        patient_dfn: Patient DFN
        station: Station number
        caller_duz: Caller DUZ
        date_from: Start date filter
        date_to: End date filter
        limit: Maximum number of procedures to return

    Returns:
        ProceduresResponse containing procedures data and metadata
    """
    start_time = datetime.now(UTC)
    station = station or get_default_station()
    caller_duz = caller_duz or get_default_duz()

    try:
        # Get patient data
        patient_data = await get_patient_data(
            vista_client=vista_client,
            station=str(station),
            patient_dfn=patient_dfn,
            caller_duz=str(caller_duz),
        )

        # Get CPT codes
        all_cpt_codes = patient_data.cpt_codes

        # Apply filters
        filtered_codes = _apply_procedure_filters(
            all_cpt_codes,
            date_from=date_from,
            date_to=date_to,
        )

        # Apply pagination
        paginated_codes, total_after_filtering = paginate_list(
            filtered_codes, offset, limit
        )

        # Build summary statistics (based on all filtered codes, not just the page)
        summary_stats = _build_procedure_summary(all_cpt_codes, filtered_codes)

        # Build RPC metadata
        end_time = datetime.now(UTC)
        rpc_details = RpcCallMetadata(
            rpc="VPR GET PATIENT DATA JSON",
            context="LHS RPC CONTEXT",
            parameters=[{"namedArray": {"patientId": patient_dfn}}],
            duz=caller_duz,
        )

        # Build response metadata
        md = ResponseMetadata(
            request_id=f"req_{int(start_time.timestamp())}",
            performance=PerformanceMetrics(
                duration_ms=int((end_time - start_time).total_seconds() * 1000),
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
            filters=ProceduresFiltersMetadata(
                date_from=date_from,
                date_to=date_to,
            ),
            pagination=PaginationMetadata(
                total_available_items=total_after_filtering,
                returned=len(paginated_codes),
                offset=offset,
                limit=limit,
                tool_name="get_patient_procedures",
                patient_dfn=patient_dfn,
            ),
        )

        # Build response data
        data = ProceduresResponseData(
            total_procedures=summary_stats["total_procedures"],
            filtered_procedures=summary_stats["filtered_procedures"],
            date_range=summary_stats["date_range"],
            unique_encounters=summary_stats["unique_encounters"],
            procedures=paginated_codes,
            filters_applied={
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
            },
        )

        return ProceduresResponse(
            success=True,
            data=data,
            metadata=md,
        )

    except VistaAPIError as e:
        logger.error(
            f"Vista API error getting procedures for patient {patient_dfn}: {e}"
        )
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
        return ProceduresResponse(
            success=False,
            error=f"Vista API error: {e.message}",
            error_code=e.error_type,
            metadata=md,
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error getting procedures for patient {patient_dfn}"
        )
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
        return ProceduresResponse(
            success=False,
            error=f"Unexpected error: {str(e)}",
            metadata=md,
        )


def _apply_procedure_filters(
    cpt_codes: list[CPTCode],
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[CPTCode]:
    """Apply filters to CPT codes list"""
    filtered = cpt_codes

    # Filter by date range
    if date_from or date_to:
        try:
            filtered = [
                code
                for code in filtered
                if code.entered is None
                or (not date_from or date_from <= code.entered.date())
                and (not date_to or code.entered.date() <= date_to)
            ]
        except ValueError as e:
            logger.warning(f"Invalid date format in filters: {e}")

    return filtered


def _format_procedures_list(
    cpt_codes: list[CPTCode],
) -> list[dict[str, Any]]:
    """Format CPT codes as a list of procedures"""
    procedures = []

    for code in cpt_codes:
        procedure: dict[str, Any] = {
            "cpt_code": code.cpt_code,
            "description": code.name,
            "procedure_date": code.entered.isoformat() if code.entered else None,
            "quantity": code.quantity,
            "facility": code.facility_name,
        }

        if code.encounter:
            procedure["encounter_uid"] = code.encounter
            procedure["encounter_name"] = code.encounter_name

        procedures.append(procedure)

    return procedures


def _group_procedures_by_encounter(cpt_codes: list[CPTCode]) -> dict[str, Any]:
    """Group procedures by encounter"""
    encounters: dict[str, dict[str, Any]] = {}
    no_encounter_codes = []

    for code in cpt_codes:
        if code.encounter:
            encounter_key = code.encounter
            if encounter_key not in encounters:
                encounters[encounter_key] = {
                    "encounter_uid": encounter_key,
                    "encounter_name": code.encounter_name,
                    "procedures": [],
                    "procedure_count": 0,
                    "total_complexity_score": 0,
                }

            procedure: dict[str, Any] = {
                "cpt_code": code.cpt_code,
                "description": code.name,
                "procedure_date": code.entered.isoformat() if code.entered else None,
                "quantity": code.quantity,
            }

            encounters[encounter_key]["procedures"].append(procedure)
            encounters[encounter_key]["procedure_count"] += 1

            # Add complexity scoring
            complexity_scores = {"low": 1, "moderate": 2, "high": 3}
            complexity_value = procedure.get("complexity", "moderate")
            if isinstance(complexity_value, str):
                encounters[encounter_key][
                    "total_complexity_score"
                ] += complexity_scores.get(complexity_value, 2)
        else:
            no_encounter_codes.append(code)

    # Format encounters
    encounter_list = list(encounters.values())

    # Add procedures without encounters
    if no_encounter_codes:
        no_encounter_procedures = _format_procedures_list(no_encounter_codes)
        return {
            "encounters": encounter_list,
            "procedures_without_encounter": no_encounter_procedures,
        }

    return {"encounters": encounter_list}


def _build_procedure_summary(
    all_codes: list[CPTCode], filtered_codes: list[CPTCode]
) -> dict[str, Any]:
    """Build summary statistics for procedures"""

    # Count by category
    category_counts: dict[str, int] = {}
    complexity_counts = {"low": 0, "moderate": 0, "high": 0}

    # Calculate date range
    if filtered_codes:
        dates = [
            entered_date for code in filtered_codes if (entered_date := code.entered)
        ]
        date_range = {
            "earliest": min(dates).isoformat() if dates else None,
            "latest": max(dates).isoformat() if dates else None,
        }
    else:
        date_range = None

    return {
        "total_procedures": len(all_codes),
        "filtered_procedures": len(filtered_codes),
        "category_breakdown": category_counts,
        "complexity_breakdown": complexity_counts,
        "date_range": date_range,
        "unique_encounters": len({c.encounter for c in filtered_codes if c.encounter}),
    }


def register_get_patient_procedures_tool(mcp, vista_client: BaseVistaClient):
    """Register the get_patient_procedures tool with the MCP server"""

    @mcp.tool()
    async def get_patient_procedures(
        patient_dfn: str,
        station: str | None = None,
        date_from: Annotated[date | None, Field(default=None)] = None,
        date_to: Annotated[date | None, Field(default=None)] = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> ProceduresResponse:
        """Get patient CPT procedure codes and billing information."""
        start_time = datetime.now(UTC)
        station = station or get_default_station()

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
            return ProceduresResponse(
                success=False,
                error="Invalid patient DFN format",
                metadata=md,
            )

        # Use default DUZ
        caller_duz = get_default_duz()

        return await get_patient_procedures_impl(
            vista_client=vista_client,
            patient_dfn=patient_dfn,
            station=str(station),
            caller_duz=str(caller_duz),
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
        )
