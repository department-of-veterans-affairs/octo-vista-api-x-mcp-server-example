"""Administrative MCP tools"""

import logging
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..api_clients.base import BaseVistaClient, VistaAPIError
from ..parsers import parse_appointments, parse_user_info
from ..utils import (
    build_metadata,
    get_default_duz,
    get_default_station,
    log_rpc_call,
    translate_vista_error,
    validate_duz,
)

logger = logging.getLogger(__name__)


def register_admin_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register administrative tools with the MCP server"""

    @mcp.tool()
    async def get_appointments(
        clinic_ien: str = "195",
        station: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Get appointments for a specific clinic

        Args:
            clinic_ien: Clinic IEN (default: 195 - Primary Care)
            station: Vista station number (default: configured default)
            start_date: Optional start date for appointment range
            end_date: Optional end date for appointment range

        Returns:
            List of appointments with patient and provider information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Build parameters
            parameters = [
                {"string": clinic_ien},
                {"string": start_date or ""},
                {"string": end_date or ""},
            ]

            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="SDES GET APPTS BY CLIN IEN 2",
                context="SDESRPC",
                parameters=parameters,
                json_result=True,  # Try to get JSON response
            )

            # Parse appointments
            appointments = parse_appointments(result)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="SDES GET APPTS BY CLIN IEN 2",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "clinic_ien": clinic_ien,
                "station": station,
                "count": len(appointments),
                "appointments": [a.model_dump() for a in appointments],
                "metadata": build_metadata(
                    station=station,
                    rpc_name="SDES GET APPTS BY CLIN IEN 2",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="SDES GET APPTS BY CLIN IEN 2",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(
                    station=station, rpc_name="SDES GET APPTS BY CLIN IEN 2"
                ),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_appointments")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(
                    station=station, rpc_name="SDES GET APPTS BY CLIN IEN 2"
                ),
            }

    @mcp.tool()
    async def get_user_profile(
        user_duz: str | None = None,
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get detailed user profile information

        Args:
            user_duz: DUZ of user to look up (default: current user)
            station: Vista station number (default: configured default)

        Returns:
            User profile with name, title, service, and contact information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()
        target_duz = user_duz or caller_duz

        # Validate DUZ
        if not validate_duz(target_duz):
            return {
                "success": False,
                "error": "Invalid DUZ format. DUZ must be numeric.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Try SDES RPC first (may return JSON)
            try:
                result = await vista_client.invoke_rpc(
                    station=station,
                    caller_duz=caller_duz,
                    rpc_name="SDES GET USER PROFILE BY DUZ",
                    context="SDESRPC",
                    parameters=[{"string": target_duz}],
                    json_result=True,
                )

                # Parse user info
                user_info = parse_user_info(result, target_duz)

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Log successful call
                log_rpc_call(
                    rpc_name="SDES GET USER PROFILE BY DUZ",
                    station=station,
                    duz=caller_duz,
                    duration_ms=duration_ms,
                    success=True,
                )

                if user_info:
                    return {
                        "success": True,
                        "user": user_info.model_dump(),
                        "metadata": build_metadata(
                            station=station,
                            rpc_name="SDES GET USER PROFILE BY DUZ",
                            duration_ms=duration_ms,
                        ),
                    }

            except Exception:
                # Fall back to basic user info RPC
                pass

            # Fall back to ORWU USERINFO
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWU USERINFO",
                parameters=[{"string": target_duz}] if target_duz != caller_duz else [],
            )

            # Parse user info
            user_info = parse_user_info(result, target_duz)

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
                    "error": f"No user information found for DUZ {target_duz}",
                    "metadata": build_metadata(station=station),
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
                "metadata": build_metadata(station=station),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_user_profile")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }

    @mcp.tool()
    async def list_team_members(
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        List all team members in the current context

        Args:
            station: Vista station number (default: configured default)

        Returns:
            List of team members with their roles and contact information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWTPD1 LISTALL",
                parameters=[],
            )

            # Parse team members
            team_members = []
            if result:
                lines = result.strip().split("\n")
                for line in lines:
                    parts = line.split("^")
                    if len(parts) >= 2:
                        member = {
                            "duz": parts[0],
                            "name": parts[1],
                            "role": parts[2] if len(parts) > 2 else None,
                            "phone": parts[3] if len(parts) > 3 else None,
                            "pager": parts[4] if len(parts) > 4 else None,
                        }
                        team_members.append(member)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWTPD1 LISTALL",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "station": station,
                "count": len(team_members),
                "team_members": team_members,
                "metadata": build_metadata(
                    station=station,
                    rpc_name="ORWTPD1 LISTALL",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWTPD1 LISTALL",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORWTPD1 LISTALL"),
            }

        except Exception as e:
            logger.exception("Unexpected error in list_team_members")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORWTPD1 LISTALL"),
            }
