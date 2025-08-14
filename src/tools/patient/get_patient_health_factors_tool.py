"""Get patient health factors tool for MCP server"""

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
    HealthFactorsResponse,
    HealthFactorsResponseData,
)
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_health_factors_tool(
    mcp: FastMCP, vista_client: BaseVistaClient
):
    """Register the get_patient_health_factors tool with the MCP server"""

    @mcp.tool()
    async def get_patient_health_factors(
        patient_dfn: str,
        station: str | None = None,
        category_filter: str | None = None,
        risk_category: str | None = None,
        severity_filter: str | None = None,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> HealthFactorsResponse:
        """Get patient health factors and risk assessments."""
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
            return HealthFactorsResponse(
                success=False,
                error=f"Invalid patient DFN: {patient_dfn}",
                metadata=md,
            )

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter health factors with combined conditions
            health_factors = [
                f
                for f in patient_data.health_factors
                if (
                    not category_filter or category_filter.upper() in f.category.upper()
                )
                and (
                    not risk_category
                    or f.risk_category.lower() == risk_category.lower()
                )
                and (
                    not severity_filter
                    or f.severity_level.lower() == severity_filter.lower()
                )
            ]

            # Apply pagination
            health_factors_page, total_health_factors_after_filtering = paginate_list(
                health_factors, offset, limit
            )

            # Group factors by risk category
            from ...services.validators.clinical_validators import (
                get_health_factor_trends,
            )

            factor_groups: dict[str, list[str]] = {}
            for factor in health_factors_page:
                group_key = factor.risk_category
                if group_key not in factor_groups:
                    factor_groups[group_key] = []
                factor_groups[group_key].append(factor.uid)

            # Identify high-risk factors
            high_risk_factors = [
                f.uid for f in health_factors_page if f.risk_score >= 7
            ]

            # Calculate trending for common factors
            trending_data = {}
            common_factor_names = list({f.factor_name for f in health_factors_page})[
                :10
            ]  # Top 10
            for factor_name in common_factor_names:
                trending_data[factor_name] = get_health_factor_trends(
                    health_factors, factor_name
                )

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
                    "category_filter": category_filter,
                    "risk_category_filter": risk_category,
                    "severity_filter": severity_filter,
                    "limit": limit,
                },
                pagination=PaginationMetadata(
                    total_available_items=total_health_factors_after_filtering,
                    returned=len(health_factors_page),
                    offset=offset,
                    limit=limit,
                    tool_name="get_patient_health_factors",
                    patient_dfn=patient_dfn,
                ),
            )

            # Build response data
            data = HealthFactorsResponseData(
                by_risk_category=dict(factor_groups),
                high_risk_factors=high_risk_factors,
                health_factors=health_factors_page,
            )

            return HealthFactorsResponse(
                success=True,
                data=data,
                metadata=md,
            )

        except Exception as e:
            logger.error(
                f"🩺 [DEBUG] Exception in get_patient_health_factors: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_health_factors")
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
            return HealthFactorsResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                metadata=md,
            )
