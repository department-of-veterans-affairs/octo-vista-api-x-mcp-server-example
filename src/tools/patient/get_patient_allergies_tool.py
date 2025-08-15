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
from ...services.validators import validate_dfn
from ...utils import get_default_duz, get_default_station, get_logger, paginate_list
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_allergies_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_allergies tool with the MCP server"""

    @mcp.tool()
    async def get_patient_allergies(
        patient_dfn: str,
        station: str | None = None,
        verified_only: bool = False,
        omit_historical: bool = True,
        offset: Annotated[int, Field(default=0, ge=0)] = 0,
        limit: Annotated[int, Field(default=10, ge=1, le=200)] = 10,
    ) -> AllergiesResponse:
        """Get patient allergies and adverse reactions with analysis."""
        start_time = datetime.now(timezone.utc)
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return AllergiesResponse(
                success=False,
                error="Invalid patient DFN format",
                error_code="INVALID_DFN",
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
                        parameters=[{"namedArray": {"patientId": patient_dfn}}],
                        duz=caller_duz,
                    ),
                    station=StationMetadata(station_number=station),
                    demographics=DemographicsMetadata(
                        patient_dfn=patient_dfn,
                        patient_name=None,
                        patient_age=None,
                    ),
                ),
            )

        try:
            # Get patient data
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter allergies based on parameters
            all_allergies = patient_data.allergies

            filtered_allergies = [
                allergy
                for allergy in all_allergies
                if (not verified_only or allergy.is_verified)
                and (not omit_historical or not allergy.historical)
            ]

            # Generate analysis
            verified_count = sum(1 for a in filtered_allergies if a.is_verified)
            unverified_count = len(filtered_allergies) - verified_count

            # Analyze by product type
            by_product_type: dict[str, int] = {}
            for allergy in filtered_allergies:
                for product in allergy.products:
                    product_name = product.name.upper()
                    # Categorize common allergen types
                    if any(
                        med in product_name
                        for med in ["PENICILLIN", "AMOXICILLIN", "ANTIBIOTIC"]
                    ):
                        category = "ANTIBIOTICS"
                    elif any(
                        food in product_name
                        for food in ["CHOCOLATE", "NUTS", "SHELLFISH", "DAIRY"]
                    ):
                        category = "FOODS"
                    elif any(env in product_name for env in ["MOLD", "POLLEN", "DUST"]):
                        category = "ENVIRONMENTAL"
                    elif any(
                        med in product_name for med in ["ASPIRIN", "IBUPROFEN", "NSAID"]
                    ):
                        category = "PAIN_MEDICATIONS"
                    else:
                        category = "OTHER"

                    by_product_type[category] = by_product_type.get(category, 0) + 1

            # Analyze by reaction type
            by_reaction_type: dict[str, int] = {}
            for allergy in filtered_allergies:
                for reaction in allergy.reactions:
                    reaction_name = reaction.name.upper()
                    # Categorize reaction types
                    if any(
                        resp in reaction_name
                        for resp in ["BREATHING", "WHEEZING", "SHORTNESS"]
                    ):
                        category = "RESPIRATORY"
                    elif any(
                        skin in reaction_name
                        for skin in ["RASH", "ITCHING", "HIVES", "SWELLING"]
                    ):
                        category = "DERMATOLOGIC"
                    elif any(
                        gi in reaction_name for gi in ["NAUSEA", "VOMITING", "DIARRHEA"]
                    ):
                        category = "GASTROINTESTINAL"
                    elif any(
                        severe in reaction_name for severe in ["ANAPHYLAXIS", "SHOCK"]
                    ):
                        category = "SEVERE"
                    else:
                        category = "OTHER"

                    by_reaction_type[category] = by_reaction_type.get(category, 0) + 1

            # Apply pagination to filtered allergies
            allergies_page, total_allergies_after_filtering = paginate_list(
                filtered_allergies, offset, limit
            )

            # Identify severe allergies (those with multiple reactions or severe reaction types)
            severe_allergies = []
            for allergy in filtered_allergies:  # Use full list for analysis
                is_severe = False

                # Check for multiple reactions
                if allergy.reaction_count > 2:
                    is_severe = True

                # Check for severe reaction types
                for reaction in allergy.reactions:
                    reaction_name = reaction.name.upper()
                    if any(
                        severe in reaction_name
                        for severe in ["ANAPHYLAXIS", "SHOCK", "BREATHING"]
                    ):
                        is_severe = True
                        break

                if is_severe:
                    severe_allergies.append(allergy.uid)

            # Build response data
            response_data = AllergiesResponseData(
                verified_count=verified_count,
                unverified_count=unverified_count,
                by_product_type=by_product_type,
                by_reaction_type=by_reaction_type,
                severe_allergies=severe_allergies,
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
                        parameters=[{"namedArray": {"patientId": patient_dfn}}],
                        duz=caller_duz,
                    ),
                    station=StationMetadata(station_number=station),
                    demographics=DemographicsMetadata(
                        patient_dfn=patient_dfn,
                        patient_name=patient_data.patient_name,
                        patient_age=patient_data.demographics.calculate_age(),
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
                        patient_dfn=patient_dfn,
                    ),
                ),
            )

        except Exception as e:
            logger.error(f"Error retrieving allergies for patient {patient_dfn}: {e}")
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return AllergiesResponse(
                success=False,
                error=f"Failed to retrieve patient allergies: {str(e)}",
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
                        parameters=[{"namedArray": {"patientId": patient_dfn}}],
                        duz=caller_duz,
                    ),
                    station=StationMetadata(station_number=station),
                    demographics=DemographicsMetadata(
                        patient_dfn=patient_dfn,
                        patient_name=None,
                        patient_age=None,
                    ),
                ),
            )
