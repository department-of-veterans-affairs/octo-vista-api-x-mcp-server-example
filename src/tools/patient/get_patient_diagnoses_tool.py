"""Get patient diagnoses tool for MCP server"""

from datetime import UTC, datetime
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
    BodySystem,
    DiagnosesResponse,
    DiagnosesResponseData,
    DiagnosisTrend,
)
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...services.validators.clinical_validators import get_diagnosis_trends
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_diagnoses_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_diagnoses tool with the MCP server"""

    @mcp.tool()
    async def get_patient_diagnoses(
        patient_dfn: str,
        station: str | None = None,
        body_system: str | None = None,
        diagnosis_type: str | None = None,
        status_filter: str | None = None,
        icd_version: str | None = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> DiagnosesResponse:
        """Get patient diagnoses with ICD codes."""
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
            return DiagnosesResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
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
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter diagnoses by parameters
            diagnoses = [
                d
                for d in patient_data.diagnoses
                if (not body_system or d.body_system.lower() == body_system.lower())
                and (
                    not diagnosis_type
                    or d.diagnosis_type.lower() == diagnosis_type.lower()
                )
                and (
                    not status_filter
                    or (
                        d.is_chronic
                        if status_filter.lower() == "chronic"
                        else d.status.lower() == status_filter.lower()
                    )
                )
                and (not icd_version or d.icd_version.upper() == icd_version.upper())
            ]

            # Apply pagination
            filtered_diagnoses_page, total_filtered_diagnoses = paginate_list(
                diagnoses, offset, limit
            )

            # Group diagnoses by body system
            diagnosis_groups: dict[str, list[str]] = {}
            for diagnosis in filtered_diagnoses_page:
                group_key = diagnosis.body_system
                if group_key not in diagnosis_groups:
                    diagnosis_groups[group_key] = []
                diagnosis_groups[group_key].append(diagnosis.uid)

            # Identify primary diagnoses
            primary_diagnoses = [d.uid for d in filtered_diagnoses_page if d.is_primary]

            # Identify chronic conditions
            chronic_diagnoses = [d.uid for d in filtered_diagnoses_page if d.is_chronic]

            # Get active diagnoses
            active_diagnoses = [
                d.uid for d in filtered_diagnoses_page if d.status.lower() == "active"
            ]

            # Calculate trending for common diagnoses
            trending_data = {}
            common_icd_codes = list(
                {d.icd_code for d in filtered_diagnoses_page if d.icd_code}
            )[
                :10
            ]  # Top 10
            for icd_code in common_icd_codes:
                trend_dict = get_diagnosis_trends(filtered_diagnoses_page, icd_code)
                # Convert body_system string to enum if present
                if "body_system" in trend_dict and trend_dict["body_system"]:
                    try:
                        trend_dict["body_system"] = BodySystem(
                            trend_dict["body_system"]
                        )
                    except ValueError:
                        # If the string doesn't match any enum value, default to OTHER
                        trend_dict["body_system"] = BodySystem.OTHER
                trending_data[icd_code] = DiagnosisTrend(**trend_dict)

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
                    "body_system_filter": body_system,
                    "diagnosis_type_filter": diagnosis_type,
                    "status_filter": status_filter,
                    "icd_version_filter": icd_version,
                    "limit": limit,
                },
                pagination=PaginationMetadata(
                    total_available_items=total_filtered_diagnoses,
                    offset=offset,
                    limit=limit,
                    returned=len(filtered_diagnoses_page),
                    tool_name="get_patient_diagnoses",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = DiagnosesResponseData(
                summary={
                    "primary_count": len(primary_diagnoses),
                    "chronic_count": len(chronic_diagnoses),
                    "active_count": len(active_diagnoses),
                    "icd_9_count": len(
                        [d for d in filtered_diagnoses_page if d.icd_version == "ICD-9"]
                    ),
                    "icd_10_count": len(
                        [
                            d
                            for d in filtered_diagnoses_page
                            if d.icd_version == "ICD-10"
                        ]
                    ),
                },
                by_body_system=diagnosis_groups,
                primary_diagnoses=primary_diagnoses,
                chronic_conditions=chronic_diagnoses,
                trending=trending_data,
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
