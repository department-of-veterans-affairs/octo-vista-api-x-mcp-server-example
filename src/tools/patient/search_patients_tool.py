"""Search patients tool for MCP server"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.responses import PatientSearchResponse
from ...services.parsers.vista import parse_patient_search
from ...services.rpc import build_single_string_param, execute_rpc
from ...utils import get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_search_patients_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the search_patients tool with the MCP server"""

    @mcp.tool()
    async def search_patients(
        search_term: str,
        station: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search patients by partial name or SSN last-4."""
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Execute RPC with standardized error handling
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="ORWPT LIST",
            parameters=build_single_string_param(f"^{search_term.upper()}"),
            parser=parse_patient_search,
            station=station,
            caller_duz=caller_duz,
            error_response_builder=lambda error, metadata: PatientSearchResponse.error_response(
                error=error,
                metadata=metadata,
            ).model_dump(),
        )

        # Check if this is an error response
        if "error" in rpc_result:
            return rpc_result

        # Get parsed data and metadata
        patients = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        # Add station to each patient
        for patient in patients:
            patient.station = station

        # Limit results
        if limit and len(patients) > limit:
            patients = patients[:limit]

        # Build response
        response = PatientSearchResponse(
            success=True,
            search_term=search_term,
            station=station,
            count=len(patients),
            patients=patients,
            metadata=metadata,
        )

        return response.model_dump()
