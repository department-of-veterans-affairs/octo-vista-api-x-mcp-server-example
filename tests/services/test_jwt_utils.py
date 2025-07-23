"""Tests for JWT token parsing utilities"""

import base64
import json
import time
from datetime import datetime, timedelta, timezone

import pytest

from src.vista.auth.jwt import (
    decode_jwt_payload,
    get_token_expiry,
    get_token_ttl_seconds,
    has_token_expired,
)


def create_test_jwt(exp_timestamp: int, additional_claims: dict | None = None) -> str:
    """Helper to create a test JWT token"""
    header = {"alg": "RS256", "typ": "JWT"}

    payload = {
        "sub": "test-user",
        "iss": "test-issuer",
        "aud": ["test-audience"],
        "exp": exp_timestamp,
        "iat": int(time.time()),
        "nbf": int(time.time()),
    }

    if additional_claims:
        payload.update(additional_claims)

    # Encode header and payload
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )

    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )

    # Create fake signature
    signature = "fake-signature"

    return f"{header_encoded}.{payload_encoded}.{signature}"


class TestDecodeJwtPayload:
    """Tests for decode_jwt_payload function"""

    def test_decode_valid_jwt(self):
        """Test decoding a valid JWT token"""
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        payload = decode_jwt_payload(token)

        assert payload["sub"] == "test-user"
        assert payload["iss"] == "test-issuer"
        assert payload["exp"] == exp_timestamp

    def test_decode_jwt_with_padding(self):
        """Test decoding JWT that needs padding"""
        # Create a token that will need padding
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        token = create_test_jwt(exp_timestamp, {"extra": "data"})

        payload = decode_jwt_payload(token)

        assert payload["sub"] == "test-user"
        assert payload["extra"] == "data"

    def test_decode_invalid_format(self):
        """Test decoding token with invalid format"""
        with pytest.raises(ValueError, match="Invalid JWT format"):
            decode_jwt_payload("invalid.token")

    def test_decode_invalid_base64(self):
        """Test decoding token with invalid base64"""
        with pytest.raises(ValueError, match="Failed to decode JWT payload"):
            decode_jwt_payload("invalid.base64!@#$.signature")


class TestGetTokenExpiry:
    """Tests for get_token_expiry function"""

    def test_get_expiry_from_valid_token(self):
        """Test extracting expiry from valid token"""
        exp_datetime = datetime.now(timezone.utc) + timedelta(hours=1)
        exp_timestamp = int(exp_datetime.timestamp())
        token = create_test_jwt(exp_timestamp)

        expiry = get_token_expiry(token)

        # Compare timestamps (allow 1 second difference for rounding)
        assert abs(expiry.timestamp() - exp_timestamp) < 1

    def test_get_expiry_missing_exp_claim(self):
        """Test token missing exp claim"""
        # Create token without exp
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {"sub": "test-user", "iss": "test-issuer"}

        header_encoded = (
            base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        )
        payload_encoded = (
            base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        )

        token = f"{header_encoded}.{payload_encoded}.signature"

        with pytest.raises(ValueError, match="missing 'exp' claim"):
            get_token_expiry(token)


class TestHasTokenExpired:
    """Tests for has_token_expired function"""

    def test_token_not_expired(self):
        """Test token that is not expired"""
        # Token expires in 1 hour
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        assert not has_token_expired(token, buffer_seconds=30)

    def test_token_expired(self):
        """Test token that is expired"""
        # Token expired 1 hour ago
        exp_timestamp = int(
            (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        assert has_token_expired(token, buffer_seconds=30)

    def test_token_expiring_within_buffer(self):
        """Test token expiring within buffer period"""
        # Token expires in 20 seconds
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(seconds=20)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        # With 30 second buffer, this should be considered expired
        assert has_token_expired(token, buffer_seconds=30)

        # With 10 second buffer, this should not be expired
        assert not has_token_expired(token, buffer_seconds=10)

    def test_invalid_token_considered_expired(self):
        """Test that invalid tokens are considered expired"""
        assert has_token_expired("invalid.token", buffer_seconds=30)


class TestGetTokenTtlSeconds:
    """Tests for get_token_ttl_seconds function"""

    def test_get_ttl_positive(self):
        """Test getting TTL for non-expired token"""
        # Token expires in 1 hour
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        ttl = get_token_ttl_seconds(token)

        # Should be approximately 3600 seconds (allow some variance)
        assert 3595 < ttl < 3605

    def test_get_ttl_negative(self):
        """Test getting TTL for expired token"""
        # Token expired 1 hour ago
        exp_timestamp = int(
            (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        ttl = get_token_ttl_seconds(token)

        # Should be negative
        assert ttl < 0

    def test_get_ttl_invalid_token(self):
        """Test getting TTL for invalid token"""
        ttl = get_token_ttl_seconds("invalid.token")

        # Should return 0 for invalid tokens
        assert ttl == 0.0
