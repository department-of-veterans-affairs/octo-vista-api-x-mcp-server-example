"""
Authentication middleware matching Vista API X filter
"""

from typing import Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.auth.token_parsers import token_parser_factory
from src.config import settings
from src.exceptions.handlers import create_error_response


class VistaApiXAuthenticationFilter(BaseHTTPMiddleware):
    """
    Authentication filter matching Vista API X behavior
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through authentication filter"""
        
        # Check for bypass header (X-UAAS-AUTH: auth-request)
        bypass_header = request.headers.get(settings.bypass_auth_header, "").lower()
        if bypass_header == settings.bypass_auth_value:
            # Bypass authentication
            response = await call_next(request)
            return response
        
        # Skip authentication for auth endpoints
        if request.url.path.startswith("/auth/"):
            response = await call_next(request)
            return response
        
        # Skip for health checks and root
        if request.url.path in ["/", "/health"]:
            response = await call_next(request)
            return response
        
        # Extract authorization header
        auth_header = request.headers.get("authorization", "")
        
        # Check if this is an RPC invocation endpoint
        if "/rpc/invoke" in request.url.path:
            if not auth_header.startswith("Bearer "):
                # Missing or invalid authorization
                return self._create_auth_error_response(
                    request,
                    "JWT-ACCESS-DENIED-0001",
                    "Missing or invalid authorization header"
                )
            
            # Extract token
            token = auth_header[7:]
            
            try:
                # Get appropriate parser based on headers
                headers_dict = dict(request.headers)
                parser = token_parser_factory.get_parser(headers_dict)
                
                # Parse and validate token
                token_payload = await parser.parse(token, headers_dict)
                
                # Store token payload in request state for later use
                request.state.token_payload = token_payload
                request.state.authenticated = True
                
            except ValueError as e:
                error_code = "JWT-INVALID"
                if "expired" in str(e).lower():
                    error_code = "JWT-EXPIRED"
                elif "signature" in str(e).lower():
                    error_code = "JWT-SIGNATURE-INVALID"
                
                return self._create_auth_error_response(
                    request,
                    error_code,
                    str(e)
                )
            except Exception as e:
                return self._create_auth_error_response(
                    request,
                    "JWT-ERROR",
                    f"Token validation failed: {str(e)}"
                )
        
        # Continue processing
        response = await call_next(request)
        return response
    
    def _create_auth_error_response(self, request: Request, error_code: str, message: str) -> Response:
        """Create authentication error response"""
        from starlette.responses import JSONResponse
        
        return JSONResponse(
            status_code=401,
            content=create_error_response(
                error_code=error_code,
                title="Unauthorized",
                message=message,
                path=str(request.url.path),
                status_code=401
            )
        )


class SecurityContext:
    """Security context for request processing"""
    
    def __init__(self, request: Request):
        self.request = request
        self._token_payload = getattr(request.state, "token_payload", None)
        self._authenticated = getattr(request.state, "authenticated", False)
    
    @property
    def is_authenticated(self) -> bool:
        """Check if request is authenticated"""
        return self._authenticated
    
    @property
    def token_payload(self) -> Optional[dict]:
        """Get token payload"""
        return self._token_payload
    
    @property
    def user(self) -> Optional[dict]:
        """Get user from token payload"""
        if self._token_payload:
            return self._token_payload.get("user", {})
        return None
    
    @property
    def authorities(self) -> list:
        """Get authorities from token"""
        if self.user:
            return self.user.get("authorities", [])
        return []
    
    @property
    def vista_ids(self) -> list:
        """Get vista IDs from token"""
        if self.user:
            return self.user.get("vistaIds", [])
        return []
    
    @property
    def flags(self) -> list:
        """Get flags from token"""
        if self._token_payload:
            return self._token_payload.get("flags", [])
        return []
    
    def has_authority(self, context: str, rpc: str) -> bool:
        """Check if user has authority for context/rpc"""
        for auth in self.authorities:
            auth_context = auth.get("context", "")
            auth_rpc = auth.get("rpc", "")
            
            # Check wildcards
            if auth_context == "*" or auth_context == context:
                if auth_rpc == "*" or auth_rpc == rpc:
                    return True
        
        return False
    
    def has_vista_access(self, station: str, duz: str) -> bool:
        """Check if user has access to station/duz"""
        # Normalize station to 3-digit
        station_3digit = station[:3] if len(station) >= 3 else station
        
        for vista_id in self.vista_ids:
            site_id = vista_id.get("siteId", "")
            user_duz = vista_id.get("duz", "")
            
            # Normalize site ID
            site_3digit = site_id[:3] if len(site_id) >= 3 else site_id
            
            # Check wildcards
            if (site_id == "*" or site_3digit == station_3digit) and \
               (user_duz == "*" or user_duz == duz):
                return True
        
        return False
    
    def has_flag(self, flag: str) -> bool:
        """Check if token has specific flag"""
        return flag in self.flags