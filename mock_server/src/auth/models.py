"""
Authentication models matching Vista API X structure
"""

from typing import Any

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    """API key credentials for token generation"""

    key: str = Field(..., description="API key for authentication")


class AuthenticationToken(BaseModel):
    """JWT token response"""

    token: str = Field(..., description="JWT bearer token")


class VistaApiResponse(BaseModel):
    """Standard Vista API response wrapper"""

    path: str = Field(..., description="Request path")
    data: dict[str, Any] = Field(..., description="Response data")


class Authority(BaseModel):
    """RPC permission authority"""

    context: str = Field(..., description="RPC context")
    rpc: str = Field(..., description="RPC name or wildcard")
    name: str | None = Field(None, description="Authority description")


class VistaId(BaseModel):
    """Station and DUZ mapping"""

    id: str = Field(..., description="Station:DUZ format")
    name: str | None = Field(None, description="Station name")


class JwtUserPrincipal(BaseModel):
    """JWT user principal matching Vista API X structure"""

    username: str = Field(..., description="Username")
    application: str = Field(..., description="Application name")
    applicationEntry: str | None = Field("", description="Application entry")
    authenticated: bool = Field(True, description="Authentication status")
    serviceAccount: bool = Field(False, description="Service account flag")
    id: str | None = Field("", description="User ID")
    firstName: str | None = Field("", description="First name")
    lastName: str | None = Field("", description="Last name")
    email: str | None = Field("", description="Email address")
    phone: str | None = Field("", description="Phone number")
    duz: str | None = Field("", description="User DUZ")
    domain: str | None = Field("", description="Domain")
    adSamAccountName: str | None = Field("", description="AD account name")
    vistaIds: list[dict[str, str]] = Field(
        default_factory=list, description="Vista IDs"
    )
    authorities: list[dict[str, str]] = Field(
        default_factory=list, description="Authorities"
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )
    flags: list[str] = Field(default_factory=list, description="Feature flags")
    ssoiToken: bool = Field(False, description="SSOI token flag")
    name: str | None = Field(None, description="Display name")


class JwtPayload(BaseModel):
    """Complete JWT payload structure"""

    sub: str = Field(..., description="Subject")
    iss: str = Field(..., description="Issuer")
    aud: list[str] = Field(..., description="Audience")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    nbf: int = Field(..., description="Not before timestamp")
    jti: str | None = Field(None, description="JWT ID")
    applicationKey: str | None = Field(None, description="Application key")
    ttl: int | None = Field(3, description="TTL in hours")
    refresh_ttl: int | None = Field(60, description="Refresh TTL in hours")
    refresh_count: int | None = Field(0, description="Refresh count")
    idType: str | None = Field("STANDARD", description="ID type")
    user: JwtUserPrincipal | None = Field(None, description="User principal")
    vamf_auth_roles: list[str] = Field(default_factory=list, alias="vamf.auth.roles")

    class Config:
        populate_by_name = True


class Permission(BaseModel):
    """DynamoDB permission structure"""

    stationNo: str = Field(..., description="Station number")
    userDuz: str = Field(..., description="User DUZ")
    contextName: str = Field(..., description="RPC context name")
    rpcName: str = Field(..., description="RPC name or wildcard")


class Station(BaseModel):
    """DynamoDB station structure"""

    stationNo: str = Field(..., description="Station number")
    userDuz: str = Field(..., description="User DUZ")


class AuthApplication(BaseModel):
    """DynamoDB AuthApplication entity"""

    appKey: str = Field(..., description="Application API key")
    appName: str = Field(..., description="Application name")
    active: bool = Field(True, description="Active status")
    permissions: list[Permission] = Field(
        default_factory=list, description="Permissions"
    )
    stations: list[Station] = Field(default_factory=list, description="Stations")
    configs: list[str] = Field(default_factory=list, description="Configuration flags")


class TokenType:
    """Token type constants"""

    STANDARD = "STANDARD"
    SSOI = "SSOI"
    REFRESH = "REFRESH"
