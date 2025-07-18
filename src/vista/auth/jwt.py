"""JWT token parsing utilities for Vista API X client"""

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """
    Decode JWT payload without verification.

    Args:
        token: JWT token string

    Returns:
        Decoded payload as dictionary

    Raises:
        ValueError: If token format is invalid
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid JWT format: expected 3 parts, got {len(parts)}")

        # Decode payload (base64url)
        payload_encoded = parts[1]

        # Add padding if needed
        padding = 4 - (len(payload_encoded) % 4)
        if padding != 4:
            payload_encoded += "=" * padding

        # Decode base64url
        payload_bytes = base64.urlsafe_b64decode(payload_encoded)
        payload = json.loads(payload_bytes)

        return payload

    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to decode JWT payload: {e}")
        raise ValueError(f"Failed to decode JWT payload: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT: {e}")
        raise ValueError(f"Unexpected error decoding JWT: {e}") from e


def get_token_expiry(token: str) -> datetime:
    """
    Extract expiry time from JWT token.

    Args:
        token: JWT token string

    Returns:
        Token expiry time as datetime

    Raises:
        ValueError: If token format is invalid or exp claim missing
    """
    payload = decode_jwt_payload(token)

    if "exp" not in payload:
        raise ValueError("JWT token missing 'exp' claim")

    exp_timestamp = payload["exp"]

    # Convert Unix timestamp to datetime
    try:
        expiry = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        return expiry
    except (ValueError, OverflowError, OSError) as e:
        raise ValueError(f"Invalid expiry timestamp {exp_timestamp}: {e}") from e


def has_token_expired(token: str, buffer_seconds: int = 30) -> bool:
    """
    Check if JWT token is expired or about to expire.

    Args:
        token: JWT token string
        buffer_seconds: Number of seconds before expiry to consider token invalid

    Returns:
        True if token is expired or will expire within buffer_seconds
    """
    try:
        expiry = get_token_expiry(token)
        now = datetime.now(timezone.utc)

        # Calculate time until expiry
        time_until_expiry = (expiry - now).total_seconds()

        # Token is expired if time until expiry is less than buffer
        is_expired = time_until_expiry <= buffer_seconds

        if is_expired:
            logger.debug(
                f"Token expired or expiring soon. Time until expiry: {time_until_expiry}s"
            )

        return is_expired

    except Exception as e:
        logger.error(f"Error checking token expiry: {e}")
        # If we can't determine expiry, consider it expired to be safe
        return True


def get_token_ttl_seconds(token: str) -> float:
    """
    Get remaining TTL (time to live) for a token in seconds.

    Args:
        token: JWT token string

    Returns:
        Remaining TTL in seconds (negative if expired)
    """
    try:
        expiry = get_token_expiry(token)
        now = datetime.now(timezone.utc)
        return (expiry - now).total_seconds()
    except Exception as e:
        logger.error(f"Error getting token TTL: {e}")
        return 0.0
