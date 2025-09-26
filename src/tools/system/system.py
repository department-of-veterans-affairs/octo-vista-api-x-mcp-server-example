"""System-level MCP tools"""

import logging
from typing import Any

from fastmcp import Context, FastMCP

from ...services.parsers.vista import (
    parse_fileman_date,
)
from ...services.rpc import (
    build_empty_params,
    build_single_string_param,
    execute_rpc,
)
from ...utils import (
    get_default_duz,
    get_default_station,
    resolve_vista_context,
)
from ...vista.base import BaseVistaClient

logger = logging.getLogger(__name__)


def register_system_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register system tools with the MCP server"""

    @mcp.tool()
    async def heartbeat(
        station: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Check Vista connection status."""
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )

        # Execute RPC with standardized error handling
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="XWB IM HERE",
            parameters=build_empty_params(),
            parser=lambda result: result == "1",
            station=station,
            caller_duz=caller_duz,
            error_response_builder=lambda error, metadata: {
                "success": False,
                "alive": False,
                "error": error,
                "metadata": metadata,
            },
        )

        # Check if this is an error response
        if "error" in rpc_result:
            return rpc_result

        # Get parsed data and metadata
        is_alive = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        return {
            "success": True,
            "alive": is_alive,
            "station": station,
            "message": (
                "Vista connection is active"
                if is_alive
                else "Vista connection check failed"
            ),
            "metadata": metadata,
        }

    @mcp.tool()
    async def get_server_time(
        station: str | None = None,
        format: str = "NOW",
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get Vista server date and time."""
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )

        # Parser function that returns both parsed and raw values
        def parse_server_time(result: str) -> dict[str, Any]:
            iso_datetime = parse_fileman_date(result.strip())
            return {
                "iso_datetime": iso_datetime,
                "fileman_time": result.strip(),
            }

        # Execute RPC with standardized error handling
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="ORWU DT",
            parameters=build_single_string_param(format),
            parser=parse_server_time,
            station=station,
            caller_duz=caller_duz,
            error_response_builder=lambda error, metadata: {
                "success": False,
                "error": error,
                "metadata": metadata,
            },
        )

        # Check if this is an error response
        if "error" in rpc_result:
            return rpc_result

        # Get parsed data and metadata
        time_data = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        return {
            "success": True,
            "station": station,
            "server_time": time_data["iso_datetime"] or time_data["fileman_time"],
            "fileman_time": time_data["fileman_time"],
            "format": format,
            "metadata": metadata,
        }

    @mcp.tool()
    async def get_server_version(
        station: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get Vista server version information."""
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )

        # Execute RPC with standardized error handling
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="ORWU VERSRV",
            parameters=build_empty_params(),
            parser=lambda result: result.strip(),
            station=station,
            caller_duz=caller_duz,
            error_response_builder=lambda error, metadata: {
                "success": False,
                "error": error,
                "metadata": metadata,
            },
        )

        # Check if this is an error response
        if "error" in rpc_result:
            return rpc_result

        # Get parsed data and metadata
        version = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        return {
            "success": True,
            "station": station,
            "version": version,
            "metadata": metadata,
        }
