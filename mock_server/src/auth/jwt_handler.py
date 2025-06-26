"""
JWT handling with RSA signing matching Vista API X
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from src.auth.models import JwtPayload, JwtUserPrincipal
from src.config import settings


class JwtHandler:
    """Handle JWT operations with RSA signing"""

    def __init__(self):
        self._private_key = None
        self._public_key = None
        self._load_keys()

    def _load_keys(self):
        """Load RSA keys from files"""
        # Load private key
        with open(settings.jwt_private_key_path, "rb") as f:
            self._private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

        # Load public key
        with open(settings.jwt_public_key_path, "rb") as f:
            self._public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())

    def generate_token(
        self,
        subject: str,
        authorities: list[dict[str, str]],
        vista_ids: list[dict[str, str]],
        flags: list[str],
        token_type: str = "STANDARD",
        ttl_hours: int | None = None,
        refresh_ttl_hours: int | None = None,
        application_key: str | None = None,
        user_data: dict[str, Any] | None = None,
    ) -> str:
        """Generate JWT token with Vista API X structure"""

        now = datetime.now(UTC)
        ttl_hours = ttl_hours or settings.jwt_ttl_hours
        refresh_ttl_hours = refresh_ttl_hours or settings.jwt_refresh_ttl_hours

        # Create user principal
        user_principal = JwtUserPrincipal(
            username=user_data.get("username", subject) if user_data else subject,
            application=user_data.get("application", "vista-api-x-mock") if user_data else "vista-api-x-mock",
            applicationEntry=user_data.get("applicationEntry", "") if user_data else "",
            authenticated=True,
            serviceAccount=user_data.get("serviceAccount", False) if user_data else False,
            id=user_data.get("id", "") if user_data else "",
            firstName=user_data.get("firstName", "") if user_data else "",
            lastName=user_data.get("lastName", "") if user_data else "",
            email=user_data.get("email", "") if user_data else "",
            phone=user_data.get("phone", "") if user_data else "",
            duz=user_data.get("duz", "") if user_data else "",
            domain=user_data.get("domain", "") if user_data else "",
            adSamAccountName=user_data.get("adSamAccountName", "") if user_data else "",
            vistaIds=vista_ids,
            authorities=authorities,
            attributes=user_data.get("attributes", {}) if user_data else {},
        )

        # Create JWT payload
        payload = JwtPayload(
            sub=subject,
            iss=settings.jwt_issuer,
            aud=[settings.jwt_audience],
            exp=int((now + timedelta(hours=ttl_hours)).timestamp()),
            iat=int(now.timestamp()),
            nbf=int(now.timestamp()),
            jti=self._generate_jti(),
            applicationKey=application_key or "vista-api-x-mock",
            ttl=ttl_hours,
            refresh_ttl=refresh_ttl_hours,
            refresh_count=0,
            idType=token_type,
            user=user_principal,
            flags=flags,
            vamf_auth_roles=[],
        )

        # Convert to dict for JWT encoding
        payload_dict = payload.model_dump(by_alias=True, exclude_none=True)

        # Encode JWT with RSA private key
        token = jwt.encode(payload_dict, self._private_key, algorithm=settings.jwt_algorithm)

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

            # Decode with public key
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
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
        refresh_window = timedelta(hours=payload.get("refresh_ttl", settings.jwt_refresh_ttl_hours))

        if now > exp + refresh_window:
            raise ValueError("Token is beyond refresh window")

        # Update token with new expiration
        payload["exp"] = int((now + timedelta(hours=payload.get("ttl", settings.jwt_ttl_hours))).timestamp())
        payload["iat"] = int(now.timestamp())
        payload["nbf"] = int(now.timestamp())
        payload["refresh_count"] = payload.get("refresh_count", 0) + 1

        # Re-encode token
        token = jwt.encode(payload, self._private_key, algorithm=settings.jwt_algorithm)

        return token

    def _generate_jti(self) -> str:
        """Generate unique JWT ID"""
        import hashlib
        import random
        import time

        data = f"{time.time()}{random.random()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Global JWT handler instance
jwt_handler = JwtHandler()
