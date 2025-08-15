"""Get patient procedures tool - retrieve CPT codes and procedure data"""

from datetime import UTC, datetime
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
from ...services.validators.cpt_validators import get_procedure_complexity
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient, VistaAPIError

logger = get_logger(__name__)


async def get_patient_procedures_impl(
    vista_client: BaseVistaClient,
    patient_dfn: str,
    station: str | None = None,
    caller_duz: str | None = None,
    procedure_category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    group_by_encounter: bool = False,
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
        procedure_category: Filter by category (surgery, radiology, pathology, etc.)
        date_from: Start date filter (YYYY-MM-DD)
        date_to: End date filter (YYYY-MM-DD)
        group_by_encounter: Group procedures by encounter
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
            procedure_category=procedure_category,
            date_from=date_from,
            date_to=date_to,
        )

        # Apply pagination
        paginated_codes, total_after_filtering = paginate_list(
            filtered_codes, offset, limit
        )

        # TODO: Implement group_by_encounter functionality using _group_procedures_by_encounter()
        # Currently, procedures are returned as raw CPTCode objects regardless of this parameter

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
                procedure_category=procedure_category,
                date_from=date_from,
                date_to=date_to,
                group_by_encounter=group_by_encounter,
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
            surgical_procedures=summary_stats["surgical_procedures"],
            diagnostic_procedures=summary_stats["diagnostic_procedures"],
            procedures_with_modifiers=summary_stats["procedures_with_modifiers"],
            category_breakdown=summary_stats["category_breakdown"],
            complexity_breakdown=summary_stats["complexity_breakdown"],
            date_range=summary_stats["date_range"],
            unique_providers=summary_stats["unique_providers"],
            unique_encounters=summary_stats["unique_encounters"],
            procedures=paginated_codes,
            filters_applied={
                "category": procedure_category,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "grouped_by_encounter": group_by_encounter,
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
    procedure_category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[CPTCode]:
    """Apply filters to CPT codes list"""
    filtered = cpt_codes

    # Filter by category
    if procedure_category:
        category_lower = procedure_category.lower()
        filtered = [
            code
            for code in filtered
            if code.procedure_category.lower() == category_lower
        ]

    # Filter by date range
    if date_from or date_to:
        try:
            from_date = (
                datetime.fromisoformat(date_from).replace(tzinfo=UTC)
                if date_from
                else datetime.min.replace(tzinfo=UTC)
            )
            to_date = (
                datetime.fromisoformat(date_to).replace(tzinfo=UTC)
                if date_to
                else datetime.max.replace(tzinfo=UTC)
            )

            filtered = [
                code for code in filtered if from_date <= code.procedure_date <= to_date
            ]
        except ValueError as e:
            logger.warning(f"Invalid date format in filters: {e}")

    return filtered


def _format_procedures_list(
    cpt_codes: list[CPTCode], include_modifiers: bool = True
) -> list[dict[str, Any]]:
    """Format CPT codes as a list of procedures"""
    procedures = []

    for code in cpt_codes:
        procedure: dict[str, Any] = {
            "cpt_code": code.cpt_code,
            "description": code.description,
            "procedure_date": code.procedure_date.isoformat(),
            "provider": code.provider,
            "quantity": code.quantity,
            "category": code.procedure_category,
            "complexity": get_procedure_complexity(code.cpt_code, code.description),
            "facility": code.facility_name,
            "status": code.status,
            "is_surgical": code.is_surgical,
            "is_diagnostic": code.is_diagnostic,
        }

        if include_modifiers and code.modifiers:
            procedure["modifiers"] = list(code.modifiers)

        if code.associated_visit_uid:
            procedure["encounter_uid"] = code.associated_visit_uid
            procedure["encounter_name"] = code.encounter_name

        if code.comments:
            procedure["comments"] = code.comments

        procedures.append(procedure)

    return procedures


def _group_procedures_by_encounter(
    cpt_codes: list[CPTCode], include_modifiers: bool = True
) -> dict[str, Any]:
    """Group procedures by encounter"""
    encounters: dict[str, dict[str, Any]] = {}
    no_encounter_codes = []

    for code in cpt_codes:
        if code.associated_visit_uid:
            encounter_key = code.associated_visit_uid
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
                "description": code.description,
                "procedure_date": code.procedure_date.isoformat(),
                "provider": code.provider,
                "quantity": code.quantity,
                "category": code.procedure_category,
                "complexity": get_procedure_complexity(code.cpt_code, code.description),
                "is_surgical": code.is_surgical,
                "is_diagnostic": code.is_diagnostic,
            }

            if include_modifiers and code.modifiers:
                procedure["modifiers"] = list(code.modifiers)

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
        no_encounter_procedures = _format_procedures_list(
            no_encounter_codes, include_modifiers
        )
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

    for code in filtered_codes:
        # Category counts
        category = code.procedure_category
        category_counts[category] = category_counts.get(category, 0) + 1

        # Complexity counts
        complexity = get_procedure_complexity(code.cpt_code, code.description)
        if complexity in complexity_counts:
            complexity_counts[complexity] += 1

    # Calculate date range
    if filtered_codes:
        dates = [code.procedure_date for code in filtered_codes]
        date_range = {
            "earliest": min(dates).isoformat(),
            "latest": max(dates).isoformat(),
        }
    else:
        date_range = None

    return {
        "total_procedures": len(all_codes),
        "filtered_procedures": len(filtered_codes),
        "surgical_procedures": len([c for c in filtered_codes if c.is_surgical]),
        "diagnostic_procedures": len([c for c in filtered_codes if c.is_diagnostic]),
        "procedures_with_modifiers": len(
            [c for c in filtered_codes if c.has_modifiers]
        ),
        "category_breakdown": category_counts,
        "complexity_breakdown": complexity_counts,
        "date_range": date_range,
        "unique_providers": len({c.provider for c in filtered_codes if c.provider}),
        "unique_encounters": len(
            {c.associated_visit_uid for c in filtered_codes if c.associated_visit_uid}
        ),
    }


def register_get_patient_procedures_tool(mcp, vista_client: BaseVistaClient):
    """Register the get_patient_procedures tool with the MCP server"""

    @mcp.tool()
    async def get_patient_procedures(
        patient_dfn: str,
        station: str | None = None,
        procedure_category: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        group_by_encounter: bool = False,
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

        # Validate limit
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
            return ProceduresResponse(
                success=False,
                error="Limit must be between 1 and 200",
                metadata=md,
            )

        # Validate date formats if provided
        if date_from:
            try:
                datetime.fromisoformat(date_from)
            except ValueError:
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
                    error="Invalid date_from format. Use YYYY-MM-DD",
                    metadata=md,
                )

        if date_to:
            try:
                datetime.fromisoformat(date_to)
            except ValueError:
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
                    error="Invalid date_to format. Use YYYY-MM-DD",
                    metadata=md,
                )

        # Validate procedure category
        valid_categories = [
            "surgery",
            "radiology",
            "pathology",
            "evaluation",
            "therapy",
            "other",
        ]
        if procedure_category and procedure_category.lower() not in valid_categories:
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
                error=f"Invalid procedure_category. Must be one of: {', '.join(valid_categories)}",
                metadata=md,
            )

        # Use default DUZ
        caller_duz = get_default_duz()

        return await get_patient_procedures_impl(
            vista_client=vista_client,
            patient_dfn=patient_dfn,
            station=str(station),
            caller_duz=str(caller_duz),
            procedure_category=procedure_category,
            date_from=date_from,
            date_to=date_to,
            group_by_encounter=group_by_encounter,
            offset=offset,
            limit=limit,
        )
