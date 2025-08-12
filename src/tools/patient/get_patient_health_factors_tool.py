"""Get patient health factors tool for MCP server"""

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.responses.tool_responses import PatientHealthFactorsResponse
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import (
    build_metadata,
    build_pagination_metadata,
    get_default_duz,
    get_default_station,
    get_logger,
)
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
        limit: int = 100,
        offset: int = 0,
    ) -> PatientHealthFactorsResponse | dict[str, Any]:
        """Get patient health factors and risk assessments."""
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        # Validate limit parameter
        if limit < 1 or limit > 200:
            return {
                "success": False,
                "error": "Limit must be between 1 and 200.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter health factors
            health_factors = patient_data.health_factors

            # Filter by category
            if category_filter:
                health_factors = [
                    f
                    for f in health_factors
                    if category_filter.upper() in f.category.upper()
                ]

            # Filter by risk category
            if risk_category:
                health_factors = [
                    f
                    for f in health_factors
                    if f.risk_category.lower() == risk_category.lower()
                ]

            # Filter by severity
            if severity_filter:
                health_factors = [
                    f
                    for f in health_factors
                    if f.severity_level.lower() == severity_filter.lower()
                ]

            # Apply pagination
            total_health_factors = len(health_factors)
            health_factors_page = health_factors[offset : offset + limit]

            # Group factors by risk category (use paginated results)
            from ...services.validators.clinical_validators import (
                get_health_factor_trends,
            )

            factor_groups: dict[str, list[Any]] = {}
            for factor in health_factors_page:
                group_key = factor.risk_category
                if group_key not in factor_groups:
                    factor_groups[group_key] = []
                factor_groups[group_key].append(factor)

            # Identify high-risk factors (from paginated results)
            high_risk_factors = [f for f in health_factors_page if f.risk_score >= 7]

            # Identify modifiable factors (from paginated results)
            modifiable_factors = [f for f in health_factors_page if f.is_modifiable]

            # Get factors requiring monitoring (from paginated results)
            monitoring_factors = [
                f for f in health_factors_page if f.requires_monitoring
            ]

            # Calculate trending for common factors (from paginated results)
            trending_data = {}
            common_factor_names = list({f.factor_name for f in health_factors_page})[
                :10
            ]  # Top 10
            for factor_name in common_factor_names:
                trending_data[factor_name] = get_health_factor_trends(
                    health_factors_page, factor_name
                )

            return PatientHealthFactorsResponse(
                success=True,
                data={
                    "patient_dfn": patient_dfn,
                    "patient_name": patient_data.patient_name,
                    "total_health_factors": len(patient_data.health_factors),
                    "filtered_count": len(health_factors_page),
                    "pagination": build_pagination_metadata(
                        total_items=total_health_factors,
                        returned_items=len(health_factors_page),
                        offset=offset,
                        limit=limit,
                        tool_name="get_patient_health_factors",
                        patient_dfn=patient_dfn,
                        station=station,
                        category_filter=category_filter,
                        risk_category=risk_category,
                        severity_filter=severity_filter,
                    ),
                    "summary": {
                        "high_risk_count": len(high_risk_factors),
                        "modifiable_count": len(modifiable_factors),
                        "monitoring_required_count": len(monitoring_factors),
                        "average_risk_score": (
                            round(
                                sum(f.risk_score for f in health_factors_page)
                                / len(health_factors_page),
                                1,
                            )
                            if health_factors_page
                            else 0.0
                        ),
                    },
                    "by_risk_category": {
                        group: {
                            "count": len(factors),
                            "average_risk_score": (
                                round(
                                    sum(f.risk_score for f in factors) / len(factors), 1
                                )
                                if factors
                                else 0.0
                            ),
                            "factors": [
                                {
                                    "name": factor.factor_name,
                                    "category": factor.category,
                                    "severity": factor.severity_level,
                                    "risk_score": factor.risk_score,
                                    "recorded_date": factor.recorded_date.isoformat(),
                                    "is_modifiable": factor.is_modifiable,
                                    "requires_monitoring": factor.requires_monitoring,
                                    "facility": factor.facility_name,
                                }
                                for factor in factors
                            ],
                        }
                        for group, factors in factor_groups.items()
                    },
                    "high_risk_factors": [
                        {
                            "name": factor.factor_name,
                            "category": factor.category,
                            "risk_category": factor.risk_category,
                            "severity": factor.severity_level,
                            "risk_score": factor.risk_score,
                            "recorded_date": factor.recorded_date.isoformat(),
                            "is_modifiable": factor.is_modifiable,
                            "comments": factor.comments,
                        }
                        for factor in high_risk_factors
                    ],
                    "trending": trending_data,
                    "all_health_factors": [
                        {
                            "id": factor.local_id,
                            "uid": factor.uid,
                            "name": factor.factor_name,
                            "category": factor.category,
                            "risk_category": factor.risk_category,
                            "severity": factor.severity_level,
                            "status": factor.status,
                            "risk_score": factor.risk_score,
                            "recorded_date": factor.recorded_date.isoformat(),
                            "recorded_by": factor.recorded_by,
                            "facility": factor.facility_name,
                            "encounter": factor.encounter_name,
                            "location": factor.location_name,
                            "comments": factor.comments,
                            "is_modifiable": factor.is_modifiable,
                            "requires_monitoring": factor.requires_monitoring,
                            "summary": factor.summary,
                        }
                        for factor in health_factors_page
                    ],
                },
                metadata={
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            )

        except Exception as e:
            logger.error(
                f"🩺 [DEBUG] Exception in get_patient_health_factors: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_health_factors")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
