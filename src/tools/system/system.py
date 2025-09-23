"""System-level MCP tools"""

import logging
import os
import subprocess
from typing import Any

from fastmcp import Context, FastMCP

from src.services.validators.vista_validators import validate_duz

from ...services.parsers.vista import (
    parse_fileman_date,
    parse_user_info,
)
from ...services.rpc import (
    build_empty_params,
    build_single_string_param,
    execute_rpc,
)
from ...utils import (
    build_metadata,
    get_default_duz,
    get_default_station,
    resolve_vista_context,
)
from ...vista.base import BaseVistaClient

logger = logging.getLogger(__name__)


def register_system_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register system tools with the MCP server"""

    @mcp.tool()
    async def get_system_info(ctx: Context | None = None) -> dict[str, Any]:
        """Return high-level server diagnostics."""
        try:
            cache_status: dict[str, Any] = {}
            try:
                from src.services.cache.local_cache_manager import (
                    get_local_cache_status,
                )

                cache_status = get_local_cache_status()
            except ImportError:
                cache_status = {"error": "Local cache manager not available"}

            info: dict[str, Any] = {
                "status": "healthy",
                "server": "Vista API MCP Server",
                "cache": cache_status,
                "vista_client": {
                    "configured": bool(getattr(vista_client, "base_url", "")),
                    "base_url": getattr(vista_client, "base_url", "not configured"),
                    "auth_url": getattr(vista_client, "auth_url", "not configured"),
                },
            }

            if ctx is not None:
                vista_meta = info["vista_client"]
                await ctx.info(
                    "System info requested",
                    extra={"vista_configured": vista_meta["configured"]},
                )

            return info
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error getting system info", exc_info=exc)
            return {"status": "error", "error": str(exc)}

    @mcp.tool()
    async def get_cache_status(ctx: Context | None = None) -> dict[str, Any]:
        """Provide cache configuration details."""
        try:
            from src.config import get_cache_config
            from src.services.cache.local_cache_manager import get_local_cache_status

            cache_config = get_cache_config()
            local_status = get_local_cache_status()

            payload = {
                "cache_config": cache_config,
                "local_status": local_status,
                "environment": {
                    "CACHE_BACKEND": os.getenv("CACHE_BACKEND", "not-set"),
                    "LOCAL_CACHE_MONITORING": os.getenv(
                        "LOCAL_CACHE_MONITORING", "false"
                    ),
                },
            }

            if ctx is not None:
                await ctx.debug(
                    "Provided cache status",
                    extra={"backend": payload["environment"]["CACHE_BACKEND"]},
                )

            return payload
        except ImportError:
            return {
                "error": "Cache services not available",
                "message": "Local cache manager or config not available",
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error getting cache status", exc_info=exc)
            return {"error": str(exc)}

    @mcp.tool()
    async def restart_local_cache(ctx: Context | None = None) -> dict[str, Any]:
        """Restart local cache infrastructure if present."""
        try:
            from src.services.cache.local_cache_manager import local_cache_manager

            compose_file = local_cache_manager.compose_file

            if compose_file.exists():
                result = subprocess.run(
                    f"docker-compose -f {compose_file} down",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    logger.info("Stopped existing local cache containers")
                else:
                    logger.warning("Failed to stop cache containers: %s", result.stderr)

            success = local_cache_manager.initialize_local_cache()
            status = local_cache_manager.get_cache_status()

            message = (
                "Local cache restarted" if success else "Failed to restart local cache"
            )

            if ctx is not None:
                await ctx.info(message)

            return {
                "success": success,
                "message": message,
                "status": status,
            }

        except ImportError:
            return {"error": "Local cache manager not available"}
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error restarting local cache", exc_info=exc)
            return {"error": str(exc)}

    @mcp.tool()
    async def get_user_profile(
        user_duz: str | None = None,
        station: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get Vista user profile information."""
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )
        target_duz = user_duz or caller_duz

        # Validate DUZ
        if not validate_duz(target_duz):
            return {
                "success": False,
                "error": "Invalid DUZ format. DUZ must be numeric.",
                "metadata": build_metadata(station=station),
            }

        # Try SDES RPC first (may return JSON)
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="SDES GET USER PROFILE BY DUZ",
            parameters=build_single_string_param(target_duz),
            parser=lambda result: parse_user_info(result, target_duz),
            station=station,
            caller_duz=caller_duz,
            context="SDESRPC",
            json_result=True,
            error_response_builder=lambda error, metadata: {
                "error": error,
                "metadata": metadata,
            },  # Suppress errors for fallback
        )

        # Check if SDES RPC succeeded and returned user info
        if "parsed_data" in rpc_result and rpc_result["parsed_data"]:
            user_info = rpc_result["parsed_data"]
            metadata = rpc_result["metadata"]
            return {
                "success": True,
                "user": user_info.model_dump(),
                "metadata": metadata,
            }

        # Fall back to ORWU USERINFO
        parameters = (
            build_single_string_param(target_duz)
            if target_duz != caller_duz
            else build_empty_params()
        )

        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="ORWU USERINFO",
            parameters=parameters,
            parser=lambda result: parse_user_info(result, target_duz),
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
        user_info = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        if user_info:
            return {
                "success": True,
                "user": user_info.model_dump(),
                "metadata": metadata,
            }
        else:
            return {
                "success": False,
                "error": f"No user information found for DUZ {target_duz}",
                "metadata": metadata,
            }

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
    async def get_intro_message(
        station: str | None = None,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Get Vista system introduction message."""
        station, caller_duz = resolve_vista_context(
            ctx,
            station_arg=station,
            default_station=get_default_station,
            default_duz=get_default_duz,
        )

        # Parser function for intro message
        def parse_intro_message(result: str) -> dict[str, Any]:
            lines = result.strip().split("\n") if result else []
            return {
                "message": result.strip(),
                "lines": lines,
            }

        # Execute RPC with standardized error handling
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="XUS INTRO MSG",
            parameters=build_empty_params(),
            parser=parse_intro_message,
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
        msg_data = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        return {
            "success": True,
            "station": station,
            "message": msg_data["message"],
            "lines": msg_data["lines"],
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
