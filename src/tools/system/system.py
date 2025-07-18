"""System-level MCP tools"""

import logging
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.parsers.vista import (
    parse_current_user,
    parse_fileman_date,
    parse_user_info,
)
from ...utils import (
    build_metadata,
    get_default_duz,
    get_default_station,
    log_rpc_call,
    translate_vista_error,
)
from ...vista.base import BaseVistaClient, VistaAPIError

logger = logging.getLogger(__name__)


def register_system_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register system tools with the MCP server"""

    @mcp.tool()
    async def get_current_user() -> dict[str, Any]:
        """
        Get the current user information

        Returns:
            Current user information including DUZ and station
        """

        start_time = time.time()
        station = get_default_station()
        caller_duz = get_default_duz()

        rpc_context = "SDECRPC"
        rpc_name = "SDES GET USER PROFILE BY DUZ"

        try:
            # Invoke RPC to get user profile
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                context=rpc_context,
                rpc_name=rpc_name,
                parameters=[{"string": caller_duz}],
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log call
            log_rpc_call(
                rpc_name=rpc_name,
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "user": parse_current_user(result),
                "station": station,
                "metadata": build_metadata(
                    station=station,
                    rpc_name=rpc_name,
                    duration_ms=duration_ms,
                ),
            }
        except VistaAPIError as e:
            log_rpc_call(
                rpc_name=rpc_name,
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "alive": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name=rpc_name),
            }
        except Exception as e:
            logger.exception("Unexpected error in get_current_user")
            return {
                "success": False,
                "alive": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name=rpc_name),
            }

    @mcp.tool()
    async def heartbeat(
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Check Vista connection status (heartbeat/keep-alive)

        Args:
            station: Vista station number (default: configured default)

        Returns:
            Connection status
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="XWB IM HERE",
                parameters=[],
            )

            # Check result (should be "1" for alive)
            is_alive = result == "1"

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log call
            log_rpc_call(
                rpc_name="XWB IM HERE",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=is_alive,
            )

            return {
                "success": True,
                "alive": is_alive,
                "station": station,
                "message": (
                    "Vista connection is active"
                    if is_alive
                    else "Vista connection check failed"
                ),
                "metadata": build_metadata(
                    station=station,
                    rpc_name="XWB IM HERE",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="XWB IM HERE",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "alive": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="XWB IM HERE"),
            }

        except Exception as e:
            logger.exception("Unexpected error in heartbeat")
            return {
                "success": False,
                "alive": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="XWB IM HERE"),
            }

    @mcp.tool()
    async def get_server_time(
        station: str | None = None,
        format: str = "NOW",
    ) -> dict[str, Any]:
        """
        Get Vista server date and time

        Args:
            station: Vista station number (default: configured default)
            format: Time format - "NOW" (current time) or "TODAY" (today's date)

        Returns:
            Server date/time in ISO format
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWU DT",
                parameters=[{"string": format}],
            )

            # Parse FileMan date
            iso_datetime = parse_fileman_date(result.strip())

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWU DT",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "station": station,
                "server_time": iso_datetime or result,
                "fileman_time": result.strip(),
                "format": format,
                "metadata": build_metadata(
                    station=station,
                    rpc_name="ORWU DT",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWU DT",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORWU DT"),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_server_time")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORWU DT"),
            }

    @mcp.tool()
    async def get_intro_message(
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get Vista system introduction message

        Args:
            station: Vista station number (default: configured default)

        Returns:
            System introduction message and version information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="XUS INTRO MSG",
                parameters=[],
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="XUS INTRO MSG",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Parse message lines
            lines = result.strip().split("\n") if result else []

            return {
                "success": True,
                "station": station,
                "message": result.strip(),
                "lines": lines,
                "metadata": build_metadata(
                    station=station,
                    rpc_name="XUS INTRO MSG",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="XUS INTRO MSG",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="XUS INTRO MSG"),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_intro_message")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="XUS INTRO MSG"),
            }

    @mcp.tool()
    async def get_user_info(
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get information about the current user

        Args:
            station: Vista station number (default: configured default)

        Returns:
            Current user information including name, title, and service
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWU USERINFO",
                parameters=[],
            )

            # Parse user info
            user_info = parse_user_info(result, caller_duz)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWU USERINFO",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            if user_info:
                # Add station
                user_info.station = station

                return {
                    "success": True,
                    "user": user_info.model_dump(),
                    "metadata": build_metadata(
                        station=station,
                        rpc_name="ORWU USERINFO",
                        duration_ms=duration_ms,
                    ),
                }
            else:
                return {
                    "success": False,
                    "error": "Unable to parse user information",
                    "metadata": build_metadata(
                        station=station, rpc_name="ORWU USERINFO"
                    ),
                }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWU USERINFO",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORWU USERINFO"),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_user_info")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORWU USERINFO"),
            }

    @mcp.tool()
    async def get_server_version(
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get Vista server version information

        Args:
            station: Vista station number (default: configured default)

        Returns:
            Server version information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWU VERSRV",
                parameters=[],
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWU VERSRV",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "station": station,
                "version": result.strip(),
                "metadata": build_metadata(
                    station=station,
                    rpc_name="ORWU VERSRV",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWU VERSRV",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORWU VERSRV"),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_server_version")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORWU VERSRV"),
            }
