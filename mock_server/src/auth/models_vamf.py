"""
VAMF-compatible JWT models matching dev environment structure
"""

from typing import Any

from pydantic import BaseModel, Field


class VamfVistaId(BaseModel):
    """Vista ID in VAMF format"""

    siteId: str = Field(..., description="Site/Station ID")
    siteName: str = Field(..., description="Site name")
    duz: str = Field(..., description="User DUZ")


class VamfJwtPayload(BaseModel):
    """JWT payload matching VAMF userservice v2 structure"""

    # Standard JWT claims
    sub: str = Field(..., description="Subject (user ID)")
    iss: str = Field(..., description="Issuer")
    aud: list[str] | str = Field(..., description="Audience")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    nbf: int = Field(..., description="Not before timestamp")
    jti: str = Field(..., description="JWT ID")

    # User information at root level
    authenticated: bool = Field(True, description="Authentication status")
    lastName: str = Field(..., description="Last name")
    firstName: str = Field(..., description="First name")
    email: str = Field(..., description="Email address")

    # Authentication details
    authenticationAuthority: str = Field(
        "gov.va.iam.ssoi.v1", description="Authentication authority"
    )
    idType: str = Field("secid", description="ID type")
    userType: str = Field("user", description="User type")
    loa: int = Field(3, description="Level of Assurance")

    # Vista information at root level
    vistaIds: list[VamfVistaId] = Field(
        default_factory=list, description="Vista site/DUZ mappings"
    )

    # Session information
    sst: int | None = Field(None, description="Session start time")
    staffDisclaimerAccepted: bool = Field(True, description="Staff disclaimer accepted")

    # Attributes
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )

    # VAMF authorization
    vamf_auth_resources: list[str] = Field(
        default_factory=list,
        alias="vamf.auth.resources",
        description="Resource access patterns",
    )
    vamf_auth_roles: list[str] = Field(
        default_factory=list, alias="vamf.auth.roles", description="User roles"
    )

    # Version
    version: float = Field(2.8, description="JWT version")

    class Config:
        populate_by_name = True


def create_vamf_jwt_payload(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    vista_ids: list[dict[str, str]],
    roles: list[str] | None = None,
    attributes: dict[str, Any] | None = None,
) -> VamfJwtPayload:
    """Create a VAMF-compatible JWT payload"""

    # Convert vista IDs to VAMF format
    vamf_vista_ids = []
    for vid in vista_ids:
        vamf_vista_ids.append(
            VamfVistaId(
                siteId=vid.get("siteId", ""),
                siteName=vid.get("siteName", f"Site #{vid.get('siteId', '')}"),
                duz=vid.get("duz", ""),
            )
        )

    # Build resource patterns based on vista IDs
    resources = []
    # Patient access
    resources.append("^.*(/)?patient[s]?(/.*)?$")
    # Staff access for the user
    resources.append(f"^.*(/)?staff/{user_id}(/.*)?$")
    # Site access
    site_ids = "|".join([v.siteId for v in vamf_vista_ids])
    if site_ids:
        resources.append(f"^.*(/)?site[s]?/(dfn-)?({site_ids})(/.*)?$")

    # Default roles if not provided
    if roles is None:
        roles = ["staff", "va", "hcp"]

    # Default attributes
    if attributes is None:
        attributes = {
            "compact": "false",
            "secid": user_id,
        }

    return VamfJwtPayload(
        sub=user_id,
        iss="gov.va.vamf.userservice.v2",
        aud=["vista-api-x"],
        exp=0,  # Will be set by JWT handler
        iat=0,  # Will be set by JWT handler
        nbf=0,  # Will be set by JWT handler
        jti="",  # Will be set by JWT handler
        authenticated=True,
        lastName=last_name.upper(),
        firstName=first_name.upper(),
        email=email.lower(),
        authenticationAuthority="gov.va.iam.ssoi.v1",
        idType="secid",
        userType="user",
        loa=3,
        vistaIds=vamf_vista_ids,
        sst=0,  # Will be set by JWT handler
        staffDisclaimerAccepted=True,
        attributes=attributes,
        vamf_auth_resources=resources,
        vamf_auth_roles=roles,
        version=2.8,
    )


def convert_authorities_to_vamf_resources(
    authorities: list[dict[str, str]],
) -> list[str]:
    """Convert Vista API X authorities to VAMF resource patterns"""

    # For mock purposes, we'll create broad patterns
    # In real implementation, this would be more specific
    resources = []

    # Check for specific contexts
    for auth in authorities:
        context = auth.get("context", "")
        # We only need context for this check

        # Add basic patterns based on context
        if context in ["LHS RPC CONTEXT", "OR CPRS GUI CHART", "*"]:
            # Full patient access
            resources.append("^.*(/)?patient[s]?(/.*)?$")
            # Staff access
            resources.append("^.*(/)?staff(/.*)?$")
            # Site access
            resources.append("^.*(/)?site[s]?(/.*)?$")
            break

    return list(set(resources))  # Remove duplicates
