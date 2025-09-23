from collections.abc import Mapping
from typing import Any

from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

from src.logging_config import get_logger
from src.utils import (
    VISTA_CONTEXT_AUTH_HEADER_KEY,
    VISTA_CONTEXT_DUZ_KEY,
    VISTA_CONTEXT_STATE_KEY,
    VISTA_CONTEXT_STATION_KEY,
)


def _sanitize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Mask sensitive header values before logging."""
    sanitized: dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() == "authorization":
            sanitized[name] = value.split()[0] if value else ""
        else:
            sanitized[name] = value
    return sanitized


class AuthMiddleware(Middleware):
    def __init__(self) -> None:
        super().__init__()
        self._logger = get_logger("mcp-auth-middleware")

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        await self._log_headers(context, headers)
        self._store_headers_in_state(context, headers)
        return await call_next(context)

    async def on_message(self, context: MiddlewareContext, call_next):
        # Pass through for other message types without interception.
        return await call_next(context)

    async def _log_headers(
        self, context: MiddlewareContext, headers: Mapping[str, str]
    ) -> None:
        if not headers:
            return
        sanitized = _sanitize_headers(headers)

        fastmcp_context = getattr(context, "fastmcp_context", None)
        message = f"Received HTTP headers: {sanitized}"

        if fastmcp_context is not None:
            try:
                await fastmcp_context.debug(message, logger_name="mcp-auth-middleware")
                return
            except Exception:
                # Fall back to standard logging if MCP logging fails.
                pass

        self._logger.debug(message)

    def _store_headers_in_state(
        self, context: MiddlewareContext, headers: Mapping[str, str]
    ) -> None:
        fastmcp_context = getattr(context, "fastmcp_context", None)
        if fastmcp_context is None:
            return

        current_state: dict[str, Any]
        try:
            existing_state = fastmcp_context.get_state(VISTA_CONTEXT_STATE_KEY)
            current_state = (
                dict(existing_state) if isinstance(existing_state, Mapping) else {}
            )
        except Exception:
            current_state = {}

        station = headers.get("x-vista-station") or headers.get("x_station")
        duz = headers.get("x-vista-duz") or headers.get("x_duz")
        auth_header = headers.get("authorization")

        if station:
            current_state[VISTA_CONTEXT_STATION_KEY] = station.strip()
        if duz:
            current_state[VISTA_CONTEXT_DUZ_KEY] = duz.strip()
        if auth_header:
            current_state[VISTA_CONTEXT_AUTH_HEADER_KEY] = auth_header.strip()

        if current_state:
            fastmcp_context.set_state(VISTA_CONTEXT_STATE_KEY, current_state)
