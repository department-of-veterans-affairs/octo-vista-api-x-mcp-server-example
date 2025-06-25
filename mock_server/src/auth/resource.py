"""
Authentication resource endpoints matching Vista API X
"""

from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional

from src.auth.models import (
    AuthenticationToken,
    Credentials,
    TokenType,
    VistaApiResponse
)
from src.auth.jwt_handler import jwt_handler
from src.auth.token_parsers import token_parser_factory
from src.database.dynamodb_client import get_dynamodb_client
from src.exceptions.handlers import create_error_response
from src.config import settings

# Create auth router
auth_router = APIRouter()


@auth_router.post("/token", response_model=VistaApiResponse)
async def generate_token(
    credentials: Credentials,
    request: Request
) -> VistaApiResponse:
    """
    Generate JWT token from API key.
    Matches Vista API X /auth/token endpoint.
    """
    try:
        # Get DynamoDB client
        db_client = get_dynamodb_client()
        
        # Look up API key
        app_data = await db_client.get_application_by_key(credentials.key)
        
        if not app_data:
            raise HTTPException(
                status_code=401,
                detail=create_error_response(
                    error_code="JWT-AUTHENTICATION-ERROR-0002",
                    title="Unauthorized",
                    message="invalid key",
                    path=str(request.url.path),
                    status_code=401
                )
            )
        
        if not app_data.active:
            raise HTTPException(
                status_code=401,
                detail=create_error_response(
                    error_code="JWT-AUTHENTICATION-ERROR-0002",
                    title="Unauthorized",
                    message="invalid key",
                    path=str(request.url.path),
                    status_code=401
                )
            )
        
        # Check for ALLOW_VISTA_API_X_TOKEN config
        if "ALLOW_VISTA_API_X_TOKEN" not in app_data.configs:
            raise HTTPException(
                status_code=401,
                detail=create_error_response(
                    error_code="JWT-AUTHENTICATION-ERROR-0002",
                    title="Unauthorized",
                    message="application key not valid for vista token usage",
                    path=str(request.url.path),
                    status_code=401
                )
            )
        
        # Convert permissions to JWT format
        authorities = []
        vista_ids = []
        
        for perm in app_data.permissions:
            authorities.append({
                "context": perm.contextName,
                "rpc": perm.rpcName
            })
        
        # Ensure unique vista IDs
        seen_ids = set()
        for station in app_data.stations:
            vista_id = f"{station.stationNo}:{station.userDuz}"
            if vista_id not in seen_ids:
                vista_ids.append({
                    "siteId": station.stationNo,
                    "duz": station.userDuz,
                    "siteName": ""
                })
                seen_ids.add(vista_id)
        
        # Generate JWT token
        token = jwt_handler.generate_token(
            subject=app_data.appName,
            authorities=authorities,
            vista_ids=vista_ids,
            flags=app_data.configs,
            token_type=TokenType.STANDARD,
            application_key=app_data.appKey,
            user_data={
                "username": app_data.appName,
                "application": "vista-api-x-mock",
                "serviceAccount": False
            }
        )
        
        # Return Vista API response format
        return VistaApiResponse(
            path=str(request.url.path),
            data={"token": token}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code="INTERNAL-ERROR",
                title="Internal Server Error",
                message=str(e),
                path=str(request.url.path),
                status_code=500
            )
        )


@auth_router.post("/refresh", response_model=VistaApiResponse)
async def refresh_token(
    request: Request,
    auth_token: AuthenticationToken
) -> VistaApiResponse:
    """
    Refresh an existing JWT token.
    Matches Vista API X /auth/refresh endpoint.
    """
    try:
        # Extract token from request body
        token = auth_token.token
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail=create_error_response(
                    error_code="JWT-ACCESS-DENIED-0001",
                    title="Unauthorized",  
                    message="Missing token",
                    path=str(request.url.path),
                    status_code=401
                )
            )
        
        # Refresh the token
        try:
            new_token = jwt_handler.refresh_token(token)
        except ValueError as e:
            if "expired" in str(e).lower():
                error_code = "JWT-EXPIRED"
                message = "token expired"
            elif "refresh window" in str(e).lower():
                error_code = "JWT-REFRESH-WINDOW-EXPIRED"
                message = "token is beyond refresh window"
            else:
                error_code = "JWT-INVALID"
                message = "invalid token"
            
            raise HTTPException(
                status_code=401,
                detail=create_error_response(
                    error_code=error_code,
                    title="Unauthorized",
                    message=message,
                    path=str(request.url.path),
                    status_code=401
                )
            )
        
        # Return Vista API response format
        return VistaApiResponse(
            path=str(request.url.path),
            data={"token": new_token}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code="INTERNAL-ERROR",
                title="Internal Server Error",
                message=str(e),
                path=str(request.url.path),
                status_code=500
            )
        )