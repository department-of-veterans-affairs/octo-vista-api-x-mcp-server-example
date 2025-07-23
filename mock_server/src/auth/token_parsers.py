"""
Token parsers for different authentication types matching Vista API X
"""

from abc import ABC, abstractmethod
from typing import Any

from src.auth.jwt_handler import jwt_handler
from src.auth.jwt_handler_vamf import vamf_jwt_handler
from src.auth.models import TokenType
from src.config import settings
from src.database.dynamodb_client import get_dynamodb_client


class TokenParser(ABC):
    """Base token parser interface"""

    @abstractmethod
    async def parse(self, token: str, headers: dict[str, str]) -> dict[str, Any]:
        """Parse and validate token"""
        pass

    @abstractmethod
    def can_parse(self, headers: dict[str, str]) -> bool:
        """Check if this parser can handle the request"""
        pass


class StandardTokenParser(TokenParser):
    """Parser for standard API key-based tokens"""

    def can_parse(self, headers: dict[str, str]) -> bool:
        """Standard parser handles requests without special headers"""
        ssoi_header = headers.get("x-octo-vista-api", "").lower()
        return not ssoi_header

    async def parse(self, token: str, headers: dict[str, str]) -> dict[str, Any]:
        """Parse standard JWT token"""
        _ = headers  # Unused parameter
        try:
            # Try VAMF handler first if configured
            if settings.jwt_use_vamf_format:
                try:
                    payload = vamf_jwt_handler.decode_token(token)
                    # Convert VAMF format to internal format for compatibility
                    return self._convert_vamf_to_internal(payload)
                except Exception:
                    # Fall back to standard handler
                    pass

            # Decode token with standard handler
            payload = jwt_handler.decode_token(token)

            # Verify token type
            if payload.get("idType") != TokenType.STANDARD:
                raise ValueError("Invalid token type for standard authentication")

            return payload

        except Exception as e:
            raise ValueError(f"Failed to parse standard token: {e!s}")

    def _convert_vamf_to_internal(self, vamf_payload: dict[str, Any]) -> dict[str, Any]:
        """Convert VAMF JWT format to internal format"""
        # Create user object from root-level fields
        user = {
            "username": vamf_payload.get("sub", ""),
            "authenticated": vamf_payload.get("authenticated", True),
            "firstName": vamf_payload.get("firstName", ""),
            "lastName": vamf_payload.get("lastName", ""),
            "email": vamf_payload.get("email", ""),
            "vistaIds": vamf_payload.get("vistaIds", []),
            "authorities": [],  # Will be populated from resources
            "attributes": vamf_payload.get("attributes", {}),
        }

        # Convert VAMF resources to authorities
        resources = vamf_payload.get("vamf.auth.resources", [])
        # For mock, if we have patient resource access, grant full permissions
        if resources and any("patient" in r for r in resources):
            user["authorities"] = [
                {"context": "LHS RPC CONTEXT", "rpc": "*"},
                {"context": "OR CPRS GUI CHART", "rpc": "*"},
            ]

        # Build payload in internal format
        return {
            **vamf_payload,
            "idType": TokenType.STANDARD,
            "user": user,
            "flags": ["ALLOW_VISTA_API_X_TOKEN"],
        }


class SsoiTokenParser(TokenParser):
    """Parser for SSOi user authentication tokens"""

    def can_parse(self, headers: dict[str, str]) -> bool:
        """SSOi parser handles requests with X-OCTO-VISTA-API header"""
        ssoi_header = headers.get("x-octo-vista-api", "").lower()
        return bool(ssoi_header)

    async def parse(self, token: str, headers: dict[str, str]) -> dict[str, Any]:
        """Parse SSOi token with magic key lookup"""
        try:
            # Get magic key from header
            magic_key = headers.get("x-octo-vista-api", "")
            if not magic_key:
                raise ValueError(
                    "Missing X-OCTO-VISTA-API header for SSOi authentication"
                )

            # Decode token (SSOi tokens are pre-validated by STS)
            # Try VAMF handler first if configured
            if settings.jwt_use_vamf_format:
                try:
                    payload = vamf_jwt_handler.decode_token(token)
                    # Convert VAMF format to internal format
                    payload = self._convert_vamf_to_internal(payload)
                except Exception:
                    # Fall back to standard handler
                    payload = jwt_handler.decode_token(token)
            else:
                payload = jwt_handler.decode_token(token)

            # Load permissions from DynamoDB using magic key
            db_client = get_dynamodb_client()
            app_data = await db_client.get_application_by_key(magic_key)

            if not app_data or not app_data.active:
                raise ValueError("Invalid or inactive magic key")

            # Merge permissions into token payload
            user_data = payload.get("user", {})

            # Convert DynamoDB permissions to JWT format
            authorities = []
            vista_ids = []

            for perm in app_data.permissions:
                authorities.append({"context": perm.contextName, "rpc": perm.rpcName})

            for station in app_data.stations:
                vista_ids.append(
                    {
                        "siteId": station.stationNo,
                        "duz": station.userDuz,
                        "siteName": "",
                    }
                )

            # Update user data with permissions
            user_data["authorities"] = authorities
            user_data["vistaIds"] = vista_ids
            payload["user"] = user_data
            payload["flags"] = app_data.configs
            payload["idType"] = TokenType.SSOI

            return payload

        except Exception as e:
            raise ValueError(f"Failed to parse SSOi token: {e!s}")

    def _convert_vamf_to_internal(self, vamf_payload: dict[str, Any]) -> dict[str, Any]:
        """Convert VAMF JWT format to internal format"""
        # Create user object from root-level fields
        user = {
            "username": vamf_payload.get("sub", ""),
            "authenticated": vamf_payload.get("authenticated", True),
            "firstName": vamf_payload.get("firstName", ""),
            "lastName": vamf_payload.get("lastName", ""),
            "email": vamf_payload.get("email", ""),
            "vistaIds": vamf_payload.get("vistaIds", []),
            "authorities": [],  # Will be populated from resources
            "attributes": vamf_payload.get("attributes", {}),
        }

        # Convert VAMF resources to authorities
        resources = vamf_payload.get("vamf.auth.resources", [])
        # For mock, if we have patient resource access, grant full permissions
        if resources and any("patient" in r for r in resources):
            user["authorities"] = [
                {"context": "LHS RPC CONTEXT", "rpc": "*"},
                {"context": "OR CPRS GUI CHART", "rpc": "*"},
            ]

        # Build payload in internal format
        return {
            **vamf_payload,
            "idType": TokenType.STANDARD,
            "user": user,
            "flags": ["ALLOW_VISTA_API_X_TOKEN"],
        }


class RefreshTokenParser(TokenParser):
    """Parser for refresh tokens"""

    def can_parse(self, headers: dict[str, str]) -> bool:
        """Refresh parser is selected explicitly, not by headers"""
        _ = headers  # Unused parameter
        return False  # Only used when explicitly refreshing

    async def parse(self, token: str, headers: dict[str, str]) -> dict[str, Any]:
        """Parse refresh token"""
        _ = headers  # Unused parameter
        try:
            # Decode token without exp verification for refresh
            # Try appropriate handler based on config
            handler = vamf_jwt_handler if settings.jwt_use_vamf_format else jwt_handler
            payload = handler.decode_token(token, verify_exp=False)

            # Verify token type allows refresh
            if payload.get("idType") not in [TokenType.STANDARD, TokenType.SSOI]:
                raise ValueError("Token type does not support refresh")

            # Check refresh count limit
            refresh_count = payload.get("refresh_count", 0)
            if refresh_count >= 10:  # Arbitrary limit
                raise ValueError("Token has reached maximum refresh count")

            return payload

        except Exception as e:
            raise ValueError(f"Failed to parse refresh token: {e!s}")


class TokenParserFactory:
    """Factory for selecting appropriate token parser"""

    def __init__(self):
        self.standard_parser = StandardTokenParser()
        self.ssoi_parser = SsoiTokenParser()
        self.refresh_parser = RefreshTokenParser()

    def get_parser(
        self, headers: dict[str, str], is_refresh: bool = False
    ) -> TokenParser:
        """Get appropriate parser based on request headers"""
        if is_refresh:
            return self.refresh_parser
        elif self.ssoi_parser.can_parse(headers):
            return self.ssoi_parser
        else:
            return self.standard_parser


# Global parser factory
token_parser_factory = TokenParserFactory()
