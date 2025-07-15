"""
Exception handlers matching Vista API X's 5 exception mappers
"""

from typing import Any, cast

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def create_error_response(
    error_code: str,
    title: str,
    message: str,
    path: str,
    status_code: int,
    error_type: str | None = None,
    fault_actor: str | None = None,
    fault_code: str | None = None,
    fault_string: str | None = None,
) -> dict[str, Any]:
    """Create error response matching Vista API X format"""

    response = {
        "success": False,
        "errorCode": error_code,
        "responseStatus": status_code,
        "title": title,
        "message": message,
        "path": path,
    }

    # Add optional fault details
    if error_type:
        response["errorType"] = error_type
    if fault_actor:
        response["faultActor"] = fault_actor
    if fault_code:
        response["faultCode"] = fault_code
    if fault_string:
        response["faultString"] = fault_string

    return response


class VistaLinkFaultException(Exception):
    """VistaLink connection/execution errors"""

    def __init__(
        self,
        message: str,
        fault_code: str = "VISTA_LINK_ERROR",
        fault_actor: str = "VistaLinkConnector",
        fault_string: str | None = None,
    ):
        self.message = message
        self.fault_code = fault_code
        self.fault_actor = fault_actor
        self.fault_string = fault_string or message
        super().__init__(self.message)


class SecurityFaultException(Exception):
    """Security/authorization errors"""

    def __init__(
        self,
        message: str,
        error_code: str = "ACCESS-DENIED",
        fault_code: str | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.fault_code = fault_code
        super().__init__(self.message)


class RpcFaultException(Exception):
    """RPC execution errors"""

    def __init__(self, message: str, rpc_name: str, fault_code: str = "RPC_ERROR"):
        self.message = message
        self.rpc_name = rpc_name
        self.fault_code = fault_code
        super().__init__(self.message)


class JwtException(Exception):
    """JWT validation errors"""

    def __init__(self, message: str, error_code: str = "JWT-INVALID"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FoundationsException(Exception):
    """General application errors"""

    def __init__(self, message: str, error_code: str = "GENERAL-ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


# Exception handlers for FastAPI


def vistalink_fault_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle VistaLink faults"""
    exc = cast(VistaLinkFaultException, exc)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="VISTA_LINK_ERROR",
            title="VistA Connection Error",
            message=exc.message,
            path=str(request.url.path),
            status_code=500,
            error_type="VistaLinkFault",
            fault_actor=exc.fault_actor,
            fault_code=exc.fault_code,
            fault_string=exc.fault_string,
        ),
    )


def security_fault_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle security faults"""
    exc = cast(SecurityFaultException, exc)
    status_code = 403 if "DENIED" in exc.error_code else 401
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            error_code=exc.error_code,
            title="Access Denied" if status_code == 403 else "Unauthorized",
            message=exc.message,
            path=str(request.url.path),
            status_code=status_code,
            error_type="SecurityFault",
            fault_code=exc.fault_code,
        ),
    )


def rpc_fault_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle RPC faults"""
    exc = cast(RpcFaultException, exc)
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            error_code="RPC_FAULT",
            title="RPC Execution Error",
            message=exc.message,
            path=str(request.url.path),
            status_code=400,
            error_type="RpcFault",
            fault_actor="RpcInvoker",
            fault_code=exc.fault_code,
            fault_string=f"RPC {exc.rpc_name} failed: {exc.message}",
        ),
    )


def jwt_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle JWT exceptions"""
    exc = cast(JwtException, exc)
    return JSONResponse(
        status_code=401,
        content=create_error_response(
            error_code=exc.error_code,
            title="JWT Authentication Error",
            message=exc.message,
            path=str(request.url.path),
            status_code=401,
            error_type="JwtException",
        ),
    )


def foundations_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general foundations exceptions"""
    exc = cast(FoundationsException, exc)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code=exc.error_code,
            title="Application Error",
            message=exc.message,
            path=str(request.url.path),
            status_code=500,
            error_type="FoundationsException",
        ),
    )


def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI HTTP exceptions in Vista API X format"""
    exc = cast(HTTPException, exc)
    # If detail is already in our format, use it directly
    if isinstance(exc.detail, dict) and "errorCode" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Otherwise, format it
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=f"HTTP-{exc.status_code}",
            title=exc.detail if isinstance(exc.detail, str) else "Error",
            message=str(exc.detail),
            path=str(request.url.path),
            status_code=exc.status_code,
        ),
    )
