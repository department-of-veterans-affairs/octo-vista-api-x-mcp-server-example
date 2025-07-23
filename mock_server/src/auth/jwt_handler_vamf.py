"""
JWT handler for VAMF-compatible tokens matching dev environment
"""

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from src.auth.models_vamf import (
    VamfJwtPayload,
    VamfVistaId,
)
from src.config import settings


class VamfJwtHandler:
    """Handle JWT operations with VAMF structure"""

    def __init__(self):
        self._private_key = None
        self._public_key = None
        self._load_keys()

    def _load_keys(self):
        """Load RSA keys from files"""
        # Load private key
        with Path(settings.jwt_private_key_path).open("rb") as f:
            self._private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

        # Load public key
        with Path(settings.jwt_public_key_path).open("rb") as f:
            self._public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )

    def generate_token(
        self,
        subject: str,
        authorities: list[dict[str, str]],  # noqa: ARG002
        vista_ids: list[dict[str, str]],
        flags: list[str],  # noqa: ARG002
        token_type: str = "STANDARD",  # noqa: ARG002
        ttl_hours: int | None = None,
        refresh_ttl_hours: int | None = None,  # noqa: ARG002
        application_key: str | None = None,  # noqa: ARG002
        user_data: dict[str, Any] | None = None,
    ) -> str:
        """Generate VAMF-compatible JWT token"""

        now = datetime.now(UTC)
        ttl_hours = ttl_hours or settings.jwt_ttl_hours

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

        # Always build standard resource patterns for VAMF tokens
        vamf_resources = []
        # Patient access
        vamf_resources.append("^.*(/)?patient[s]?(/.*)?$")
        # Staff access for the user
        vamf_resources.append(f"^.*(/)?staff/{subject}(/.*)?$")
        # Site access with actual site IDs
        site_ids = "|".join([v.siteId for v in vamf_vista_ids])
        if site_ids:
            vamf_resources.append(f"^.*(/)?site[s]?/(dfn-)?({site_ids})(/.*)?$")

        # Default roles
        roles = ["staff", "va", "hcp"]

        # Build attributes
        attributes = {
            "compact": "false",
            "secid": subject,
        }

        # Add AD attributes if available
        if user_data:
            if user_data.get("adSamAccountName"):
                attributes["adSamAccountName"] = user_data["adSamAccountName"]
            if user_data.get("email"):
                attributes["adUpn"] = user_data["email"]

        # Create VAMF JWT payload
        payload = VamfJwtPayload(
            sub=subject,
            iss="gov.va.vamf.userservice.v2",
            aud=["vista-api-x"],
            exp=int((now + timedelta(hours=ttl_hours)).timestamp()),
            iat=int(now.timestamp()),
            nbf=int(now.timestamp()),
            jti=str(uuid.uuid4()),
            authenticated=True,
            lastName=(
                user_data.get("lastName", "USER") if user_data else "USER"
            ).upper(),
            firstName=(
                user_data.get("firstName", "TEST") if user_data else "TEST"
            ).upper(),
            email=(
                user_data.get("email", f"{subject}@va.gov")
                if user_data
                else f"{subject}@va.gov"
            ).lower(),
            authenticationAuthority="gov.va.iam.ssoi.v1",
            idType="secid",
            userType="user",
            loa=3,
            vistaIds=vamf_vista_ids,
            sst=int(now.timestamp()),
            staffDisclaimerAccepted=True,
            attributes=attributes,
            vamf_auth_resources=vamf_resources,
            vamf_auth_roles=roles,
            version=2.8,
        )

        # Convert to dict for JWT encoding
        payload_dict = payload.model_dump(by_alias=True, exclude_none=True)

        # Encode JWT with RSA private key
        token = jwt.encode(
            payload_dict, self._private_key, algorithm=settings.jwt_algorithm
        )

        return token

    def decode_token(self, token: str, verify_exp: bool = True) -> dict[str, Any]:
        """Decode and verify JWT token"""

        try:
            # Add clock skew tolerance
            options = {
                "verify_exp": verify_exp,
                "verify_aud": True,
                "verify_iss": True,
                "require": ["exp", "iat", "sub", "iss", "aud"],
            }

            # Decode with public key - accept both issuers for compatibility
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[settings.jwt_algorithm],
                audience=["vista-api-x", settings.jwt_audience],
                issuer=["gov.va.vamf.userservice.v2", settings.jwt_issuer],
                options=options,
                leeway=timedelta(seconds=settings.jwt_clock_skew_seconds),
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidAudienceError:
            raise ValueError("Invalid token audience")
        except jwt.InvalidIssuerError:
            raise ValueError("Invalid token issuer")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e!s}")

    def refresh_token(self, token: str) -> str:
        """Refresh an existing token"""

        # Decode without exp verification
        payload = self.decode_token(token, verify_exp=False)

        # Check if token is expired beyond refresh window
        now = datetime.now(UTC)
        exp = datetime.fromtimestamp(payload["exp"], UTC)

        # For VAMF, use a standard refresh window
        refresh_window = timedelta(hours=settings.jwt_refresh_ttl_hours)

        if now > exp + refresh_window:
            raise ValueError("Token is beyond refresh window")

        # Update token with new expiration
        payload["exp"] = int(
            (now + timedelta(hours=settings.jwt_ttl_hours)).timestamp()
        )
        payload["iat"] = int(now.timestamp())
        payload["nbf"] = int(now.timestamp())
        payload["sst"] = int(now.timestamp())

        # Re-encode token
        token = jwt.encode(payload, self._private_key, algorithm=settings.jwt_algorithm)

        return token


# Global VAMF JWT handler instance
vamf_jwt_handler = VamfJwtHandler()
