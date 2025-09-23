"""Utility functions for Vista API MCP Server"""

import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from fastmcp import Context

from src.logging_config import get_logger

logger = get_logger()


VISTA_CONTEXT_STATE_KEY = "vista_request_context"
VISTA_CONTEXT_STATION_KEY = "station"
VISTA_CONTEXT_DUZ_KEY = "duz"
VISTA_CONTEXT_AUTH_HEADER_KEY = "authorization_header"


# Default configurations
DEFAULT_STATIONS = {
    "500": {
        "name": "Washington DC VAMC",
        "duz": "10000000219",
        "timezone": "America/New_York",
    },
    "508": {
        "name": "Atlanta VAMC",
        "duz": "10000000220",
        "timezone": "America/New_York",
    },
    "640": {
        "name": "Palo Alto VAMC",
        "duz": "10000000221",
        "timezone": "America/Los_Angeles",
    },
}


def get_default_station() -> str:
    """Get default station from environment or use 500"""
    return os.getenv("DEFAULT_STATION", "500")


def get_default_duz() -> str:
    """Get default DUZ from environment or use station default"""
    station = get_default_station()
    station_info = DEFAULT_STATIONS.get(station, DEFAULT_STATIONS["500"])
    return os.getenv("DEFAULT_DUZ", station_info["duz"])


def get_station_info(station: str) -> dict[str, str]:
    """Get station information"""
    return DEFAULT_STATIONS.get(
        station,
        {
            "name": f"Station {station}",
            "duz": get_default_duz(),
            "timezone": "America/New_York",
        },
    )


def translate_vista_error(error: Exception | dict[str, Any]) -> str:
    """
    Translate Vista API errors to user-friendly messages

    Args:
        error: Exception or error dictionary

    Returns:
        User-friendly error message
    """
    if isinstance(error, dict):
        error_type = error.get("errorType", "Unknown")
        message = error.get("message", "An error occurred")

        # Common error translations
        if error_type == "SecurityFault":
            if "permission" in message.lower():
                return "You don't have permission to perform this operation. Please check your access rights."
            elif "station" in message.lower():
                return "Access denied to the requested station. Please verify station access."
            else:
                return "Security error: Access denied."

        elif error_type == "VistaLinkFault":
            if "connect" in message.lower():
                return "Cannot connect to VistA system. The station may be offline or unreachable."
            elif "timeout" in message.lower():
                return "Connection to VistA timed out. Please try again."
            else:
                return f"VistA connection error: {message}"

        elif error_type == "RpcFault":
            if "not found" in message.lower():
                return "The requested operation is not available."
            elif "parameter" in message.lower():
                return "Invalid parameters provided for the operation."
            else:
                return f"Operation failed: {message}"

        elif error_type == "JwtException":
            return "Authentication error. Please check your credentials."

        else:
            return f"{error_type}: {message}"

    else:
        # Handle exception objects
        return str(error)


def format_timestamp(dt: datetime | None = None) -> str:
    """Format timestamp for responses"""
    if dt is None:
        dt = datetime.now(UTC)
    return dt.isoformat()


def build_metadata(
    station: str | None = None,
    rpc_name: str | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any]:
    """Build standard metadata for responses"""
    metadata: dict[str, Any] = {
        "timestamp": format_timestamp(),
        "source": "VistA RPC",
    }

    if station:
        metadata["station"] = station
        station_info = get_station_info(station)
        if station_info:
            metadata["station_name"] = station_info.get("name", f"Station {station}")

    if rpc_name:
        metadata["rpc"] = rpc_name

    if duration_ms is not None:
        metadata["duration_ms"] = duration_ms

    return metadata


def build_rpc_url(station: str, caller_duz: str) -> str | None:
    """Build RPC invoke URL if base URL is available"""
    base_url = os.getenv("VISTA_API_URL", "")
    if not base_url:
        return None
    return f"{base_url}/vista-api-x/vista-sites/{station}/users/{caller_duz}/rpc/invoke"


def create_rpc_parameter(
    value: str | list[str] | dict[str, str],
) -> dict[str, Any]:
    """
    Create RPC parameter in correct format

    Args:
        value: Parameter value (string, list, or dict)

    Returns:
        Formatted parameter dictionary
    """
    if isinstance(value, str):
        return {"string": value}
    elif isinstance(value, list):
        return {"array": value}
    else:  # dict[str, str]
        return {"named_array": value}


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return os.getenv("VISTA_MCP_DEBUG", "").lower() in ["true", "1", "yes"]


T = TypeVar("T")


def paginate_list(
    items: list[T], offset: int = 0, limit: int = 10
) -> tuple[list[T], int]:
    """
    Apply pagination to a list of items.

    Args:
        items: List of items to paginate
        offset: Starting index for pagination
        limit: Maximum number of items to return

    Returns:
        Tuple of (paginated items, total count after filtering)
    """

    if offset < 0 or limit < 1:
        raise ValueError("Offset must be non-negative and limit must be positive")
    total_items = len(items)
    paginated_items = items[offset : offset + limit]
    return paginated_items, total_items


def resolve_vista_context(
    ctx: Context | None,
    station_arg: str | None = None,
    duz_arg: str | None = None,
    default_station: Callable[[], str] | None = None,
    default_duz: Callable[[], str] | None = None,
) -> tuple[str, str]:
    """Resolve VistA station and DUZ using context state or fallbacks."""

    station = station_arg.strip() if isinstance(station_arg, str) else ""
    duz = duz_arg.strip() if isinstance(duz_arg, str) else ""

    fallback_station = default_station or get_default_station
    fallback_duz = default_duz or get_default_duz

    if ctx is not None:
        try:
            state = ctx.get_state(VISTA_CONTEXT_STATE_KEY)
        except Exception:
            state = None

        if isinstance(state, dict):
            if not station:
                candidate_station = state.get(VISTA_CONTEXT_STATION_KEY)
                if isinstance(candidate_station, str) and candidate_station.strip():
                    station = candidate_station.strip()
            if not duz:
                candidate_duz = state.get(VISTA_CONTEXT_DUZ_KEY)
                if isinstance(candidate_duz, str) and candidate_duz.strip():
                    duz = candidate_duz.strip()

    if not station:
        station = fallback_station()
    if not duz:
        duz = fallback_duz()

    logger.debug(
        "Resolved Vista context",
        extra={
            "station": station,
            "duz": duz,
        },
    )

    return station, duz


def log_rpc_call(
    rpc_name: str,
    station: str,
    duz: str,
    parameters: list[dict[str, Any]] | None = None,
    duration_ms: int | None = None,
    success: bool = True,
    error: str | None = None,
):
    """Log RPC call for audit trail"""
    from src.logging_config import log_rpc_call as log_rpc_call_structured

    log_rpc_call_structured(
        logger=logger,
        rpc_name=rpc_name,
        station=station,
        duz=duz,
        duration_ms=duration_ms,
        success=success,
        error=error,
        parameters=parameters if is_debug_mode() else None,
    )
