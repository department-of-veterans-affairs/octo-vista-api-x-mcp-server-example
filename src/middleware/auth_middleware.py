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
        headers = get_http_headers() or {}
        await self._log_headers(context, headers)
        await self._store_headers_in_state(context, headers)
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

    async def _store_headers_in_state(
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

        lowered_headers = {key.lower(): value for key, value in headers.items()}

        def _first_present(keys: tuple[str, ...]) -> str | None:
            for key in keys:
                value = lowered_headers.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return None

        station = _first_present(
            (
                "x-vista-station",
                "x_vista_station",
                "x-vista_station",
                "x_station",
            )
        )
        duz = _first_present(("x-vista-duz", "x_vista_duz", "x-duz", "x_duz"))
        auth_header = _first_present(("authorization",))

        if station:
            current_state[VISTA_CONTEXT_STATION_KEY] = station
        if duz:
            current_state[VISTA_CONTEXT_DUZ_KEY] = duz
        if auth_header:
            current_state[VISTA_CONTEXT_AUTH_HEADER_KEY] = auth_header

        if current_state:
            fastmcp_context.set_state(VISTA_CONTEXT_STATE_KEY, current_state)

            effective_station = current_state.get(VISTA_CONTEXT_STATION_KEY)
            effective_duz = current_state.get(VISTA_CONTEXT_DUZ_KEY)
            effective_auth = current_state.get(VISTA_CONTEXT_AUTH_HEADER_KEY)

            station_log = effective_station or "(missing)"
            duz_log = effective_duz or "(missing)"
            auth_present = bool(effective_auth)

            updated_fields: list[str] = []
            if station:
                updated_fields.append("station")
            if duz:
                updated_fields.append("duz")
            if auth_header:
                updated_fields.append("authorization")
            updated_fields = updated_fields or ["none"]

            message = (
                "Stored request-scoped VistA context from HTTP headers: "
                f"station={station_log}, duz={duz_log}, auth_header_present={auth_present}, "
                f"updated_fields={','.join(updated_fields)}"
            )

            self._logger.info(
                message,
                extra={
                    "station": station_log,
                    "duz": duz_log,
                    "auth_header_present": auth_present,
                },
            )

            try:
                await fastmcp_context.info(message, logger_name="mcp-auth-middleware")
            except Exception:
                # MCP info logging is best-effort
                self._logger.debug(
                    "fastmcp_context.info failed; continuing with server-only logging",
                    exc_info=True,
                )
        else:
            self._logger.debug(
                "No VistA context headers found to store",
                extra={"headers_present": bool(headers)},
            )
