"""
Authentication models matching Vista API X structure
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Credentials(BaseModel):
    """API key credentials for token generation"""
    key: str = Field(..., description="API key for authentication")

class AuthenticationToken(BaseModel):
    """JWT token response"""
    token: str = Field(..., description="JWT bearer token")

class VistaApiResponse(BaseModel):
    """Standard Vista API response wrapper"""
    path: str = Field(..., description="Request path")
    data: Dict[str, Any] = Field(..., description="Response data")

class Authority(BaseModel):
    """RPC permission authority"""
    context: str = Field(..., description="RPC context")
    rpc: str = Field(..., description="RPC name or wildcard")
    name: Optional[str] = Field(None, description="Authority description")

class VistaId(BaseModel):
    """Station and DUZ mapping"""
    id: str = Field(..., description="Station:DUZ format")
    name: Optional[str] = Field(None, description="Station name")

class JwtUserPrincipal(BaseModel):
    """JWT user principal matching Vista API X structure"""
    username: str = Field(..., description="Username")
    application: str = Field(..., description="Application name")
    applicationEntry: Optional[str] = Field("", description="Application entry")
    authenticated: bool = Field(True, description="Authentication status")
    serviceAccount: bool = Field(False, description="Service account flag")
    id: Optional[str] = Field("", description="User ID")
    firstName: Optional[str] = Field("", description="First name")
    lastName: Optional[str] = Field("", description="Last name")
    email: Optional[str] = Field("", description="Email address")
    phone: Optional[str] = Field("", description="Phone number")
    duz: Optional[str] = Field("", description="User DUZ")
    domain: Optional[str] = Field("", description="Domain")
    adSamAccountName: Optional[str] = Field("", description="AD account name")
    vistaIds: List[Dict[str, str]] = Field(default_factory=list, description="Vista IDs")
    authorities: List[Dict[str, str]] = Field(default_factory=list, description="Authorities")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")

class JwtPayload(BaseModel):
    """Complete JWT payload structure"""
    sub: str = Field(..., description="Subject")
    iss: str = Field(..., description="Issuer")
    aud: List[str] = Field(..., description="Audience")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    nbf: int = Field(..., description="Not before timestamp")
    jti: Optional[str] = Field(None, description="JWT ID")
    applicationKey: Optional[str] = Field(None, description="Application key")
    ttl: Optional[int] = Field(3, description="TTL in hours")
    refresh_ttl: Optional[int] = Field(60, description="Refresh TTL in hours")
    refresh_count: Optional[int] = Field(0, description="Refresh count")
    idType: Optional[str] = Field("STANDARD", description="ID type")
    user: Optional[JwtUserPrincipal] = Field(None, description="User principal")
    flags: List[str] = Field(default_factory=list, description="Feature flags")
    vamf_auth_roles: List[str] = Field(default_factory=list, alias="vamf.auth.roles")
    
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
    permissions: List[Permission] = Field(default_factory=list, description="Permissions")
    stations: List[Station] = Field(default_factory=list, description="Stations")
    configs: List[str] = Field(default_factory=list, description="Configuration flags")

class TokenType:
    """Token type constants"""
    STANDARD = "STANDARD"
    SSOI = "SSOI"
    REFRESH = "REFRESH"