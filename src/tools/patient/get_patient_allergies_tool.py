"""Get patient allergies tool for MCP server"""

from datetime import datetime, timezone
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ...models.responses.metadata import (
    AllergiesFiltersMetadata,
    DemographicsMetadata,
    PaginationMetadata,
    PerformanceMetrics,
    ResponseMetadata,
    RpcCallMetadata,
    StationMetadata,
)
from ...models.responses.tool_responses import (
    AllergiesResponse,
    AllergiesResponseData,
)
from ...services.data import get_patient_data
from ...services.rpc import build_icn_only_named_array_param
from ...services.validators import validate_icn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_allergies_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_allergies tool with the MCP server"""

    @mcp.tool()
    async def get_patient_allergies(
        patient_icn: str,
        station: str | None = None,
        verified_only: bool = False,
        omit_historical: bool = True,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> AllergiesResponse:
        """Get patient allergies and adverse reactions."""
        start_time = datetime.now(timezone.utc)
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate ICN
        if not validate_icn(patient_icn):
            return AllergiesResponse(
                success=False,
                error="Invalid patient ICN format",
                error_code="INVALID_ICN",
                metadata=ResponseMetadata(
                    request_id=f"req_{int(start_time.timestamp())}",
                    performance=PerformanceMetrics(
                        start_time=start_time,
                        end_time=datetime.now(timezone.utc),
                        duration_ms=0,
                    ),
                    rpc=RpcCallMetadata(
                        rpc="VPR GET PATIENT DATA JSON",
                        context="LHS RPC CONTEXT",
                        parameters=build_icn_only_named_array_param(patient_icn),
                        duz=caller_duz,
                    ),
                    station=StationMetadata(station_number=station),
                    demographics=DemographicsMetadata(
                        patient_icn=patient_icn,
                        patient_name=None,
                        patient_age=None,
                    ),
                ),
            )

        try:
            # Get patient data
            patient_data = await get_patient_data(
                vista_client, station, patient_icn, caller_duz
            )

            # Filter allergies based on parameters
            all_allergies = patient_data.allergies

            filtered_allergies = [
                allergy
                for allergy in all_allergies
                if (not verified_only or allergy.is_verified)
                and (not omit_historical or not allergy.historical)
            ]

            # Apply pagination to filtered allergies
            allergies_page, total_allergies_after_filtering = paginate_list(
                filtered_allergies, offset, limit
            )

            # Build response data
            response_data = AllergiesResponseData(
                allergies=allergies_page,  # Use paginated list
            )

            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return AllergiesResponse(
                success=True,
                data=response_data,
                metadata=ResponseMetadata(
                    request_id=f"req_{int(start_time.timestamp())}",
                    performance=PerformanceMetrics(
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                    ),
                    rpc=RpcCallMetadata(
                        rpc="VPR GET PATIENT DATA JSON",
                        context="LHS RPC CONTEXT",
                        parameters=build_icn_only_named_array_param(patient_icn),
                        duz=caller_duz,
                    ),
                    station=StationMetadata(station_number=station),
                    demographics=DemographicsMetadata(
                        patient_icn=patient_icn,
                        patient_name=patient_data.patient_name,
                        patient_age=patient_data.demographics.calculate_age(),
                        patient_gender=patient_data.demographics.gender_name,
                    ),
                    filters=AllergiesFiltersMetadata(
                        verified_only=verified_only,
                        omit_historical=omit_historical,
                    ),
                    pagination=PaginationMetadata(
                        total_available_items=total_allergies_after_filtering,
                        returned=len(allergies_page),
                        offset=offset,
                        limit=limit,
                        tool_name="get_patient_allergies",
                        patient_icn=patient_icn,
                    ),
                ),
            )

        except Exception as e:
            logger.error(f"Error retrieving allergies for patient {patient_icn}: {e}")
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return AllergiesResponse(
                success=False,
                error=f"Failed to retrieve patient allergies: {e}",
                error_code="RETRIEVAL_ERROR",
                metadata=ResponseMetadata(
                    request_id=f"req_{int(start_time.timestamp())}",
                    performance=PerformanceMetrics(
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                    ),
                    rpc=RpcCallMetadata(
                        rpc="VPR GET PATIENT DATA JSON",
                        context="LHS RPC CONTEXT",
                        parameters=build_icn_only_named_array_param(patient_icn),
                        duz=caller_duz,
                    ),
                    station=StationMetadata(station_number=station),
                    demographics=DemographicsMetadata(
                        patient_icn=patient_icn,
                        patient_name=None,
                        patient_age=None,
                    ),
                ),
            )
