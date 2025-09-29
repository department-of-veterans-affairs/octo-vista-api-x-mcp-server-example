"""Context-aware Vista API client wrapper for handling client JWT"""

import json
from contextvars import ContextVar
from typing import Any

from fastmcp.exceptions import ToolError

from ..config import USE_CLIENT_JWT
from ..logging_config import get_logger
from .auth.jwt import has_token_expired
from .base import BaseVistaClient

logger = get_logger(__name__)

# Context variable to store current request JWT
current_jwt: ContextVar[str | None] = ContextVar("current_jwt", default=None)


class ContextAwareVistaClient(BaseVistaClient):
    """Wrapper for Vista API client that handles client JWT from context"""

    def __init__(self, wrapped_client: BaseVistaClient):
        super().__init__(wrapped_client.timeout)
        self.wrapped_client = wrapped_client

    async def invoke_rpc(
        self,
        station: str,
        caller_duz: str,
        rpc_name: str,
        context: str = "OR CPRS GUI CHART",
        parameters: list[dict[str, Any]] | None = None,
        json_result: bool = False,
        use_cache: bool = True,
        **kwargs,
    ) -> Any:
        """Invoke RPC with automatic client JWT handling"""

        client_jwt = None

        logger.info(
            f"CONTEXT_AWARE_CLIENT_DEBUG: {json.dumps({
            'USE_CLIENT_JWT': USE_CLIENT_JWT,
            'station': station,
            'caller_duz': caller_duz,
            'rpc_name': rpc_name
        })}"
        )

        if USE_CLIENT_JWT:
            # Get JWT from context variable
            client_jwt = current_jwt.get()

            logger.info(
                f"CLIENT_JWT_CHECK: {json.dumps({
                'client_jwt_present': bool(client_jwt),
                'client_jwt_length': len(client_jwt) if client_jwt else 0
            })}"
            )

            if not client_jwt:
                raise ToolError(
                    "Authentication required: No JWT token provided in authorization header. "
                    "Please include 'Authorization: Bearer <token>' in your request."
                )

            # Validate JWT is not expired (30 second buffer for clock skew)
            if has_token_expired(client_jwt, buffer_seconds=30):
                raise ToolError(
                    "Authentication failed: JWT token has expired. "
                    "Please refresh your token and retry."
                )

            # Pass JWT to the wrapped client
            kwargs["client_jwt"] = client_jwt
            logger.info(
                f"CLIENT_JWT_PASSED: {json.dumps({'client_jwt_passed_to_wrapped': True})}"
            )
        else:
            logger.info(
                f"CLIENT_JWT_MODE: {json.dumps({'USE_CLIENT_JWT': False, 'mode': 'service_to_service'})}"
            )

        # Delegate to wrapped client
        logger.info(
            f"INVOKING_RPC_WITH: {json.dumps({'has_client_jwt': 'client_jwt' in kwargs})}"
        )
        return await self.wrapped_client.invoke_rpc(
            station=station,
            caller_duz=caller_duz,
            rpc_name=rpc_name,
            context=context,
            parameters=parameters,
            json_result=json_result,
            use_cache=use_cache,
            **kwargs,
        )

    async def close(self) -> None:
        """Close the wrapped client"""
        await self.wrapped_client.close()


def set_context_jwt(jwt_token: str | None) -> None:
    """Set JWT token in context for current async task"""
    current_jwt.set(jwt_token)


def get_context_jwt() -> str | None:
    """Get JWT token from context for current async task"""
    return current_jwt.get()
