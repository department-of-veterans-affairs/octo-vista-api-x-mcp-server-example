"""Tests for Vista client token refresh functionality"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.api_clients.vista_client import VistaAPIClient
from tests.test_jwt_utils import create_test_jwt


@pytest.mark.asyncio
class TestVistaClientTokenRefresh:
    """Test token refresh functionality in Vista client"""

    @staticmethod
    def get_cache_key(vista_client):
        """Helper to get the token cache key for a client"""
        return f"token_{vista_client.api_key}"

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client"""
        client = AsyncMock()
        return client

    @pytest.fixture
    def vista_client(self, mock_httpx_client):
        """Create Vista client with mocked httpx"""
        with patch(
            "src.api_clients.vista_client.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_httpx_client

            client = VistaAPIClient(
                base_url="http://localhost:9000",
                api_key="test-key",
                auth_url="http://localhost:9000",
                timeout=30.0,
            )

            # Replace the client with our mock
            client.client = mock_httpx_client

            return client

    async def test_proactive_token_refresh(self, vista_client, mock_httpx_client):
        """Test that tokens are refreshed proactively before expiry"""
        # Create a token that expires in 20 seconds (less than default 30s buffer)
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(seconds=20)).timestamp()
        )
        expiring_token = create_test_jwt(exp_timestamp)

        # Create a fresh token that expires in 1 hour
        fresh_exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        fresh_token = create_test_jwt(fresh_exp_timestamp)

        # Mock the auth endpoint to return tokens
        auth_response = AsyncMock()
        auth_response.status_code = 200
        auth_response.json = Mock(return_value={"data": {"token": fresh_token}})
        auth_response.raise_for_status = MagicMock()

        # Mock RPC response
        rpc_response = AsyncMock()
        rpc_response.status_code = 200
        rpc_response.json = Mock(return_value={"payload": {"result": "test-result"}})
        rpc_response.raise_for_status = MagicMock()

        # First call returns expiring token, second returns fresh token
        mock_httpx_client.post.side_effect = [
            auth_response,  # First auth call
            rpc_response,  # RPC call
        ]

        # Pre-populate cache with expiring token
        cache_key = self.get_cache_key(vista_client)
        vista_client.token_cache[cache_key] = expiring_token

        # Make RPC call
        await vista_client.invoke_rpc(
            station="500",
            caller_duz="123",
            rpc_name="TEST_RPC",
        )

        # Should have called auth endpoint to refresh token
        assert mock_httpx_client.post.call_count == 2

        # First call should be to auth endpoint
        auth_call = mock_httpx_client.post.call_args_list[0]
        assert "/vista-api-x/auth/token" in auth_call[0][0]

        # Second call should be RPC with fresh token
        rpc_call = mock_httpx_client.post.call_args_list[1]
        assert "Bearer" in rpc_call[1]["headers"]["Authorization"]
        assert "/rpc/invoke" in rpc_call[0][0]

    async def test_no_refresh_for_valid_token(self, vista_client, mock_httpx_client):
        """Test that valid tokens are not refreshed unnecessarily"""
        # Create a token that expires in 2 hours (well beyond buffer)
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(hours=2)).timestamp()
        )
        valid_token = create_test_jwt(exp_timestamp)

        # Mock RPC response
        rpc_response = AsyncMock()
        rpc_response.status_code = 200
        rpc_response.json = Mock(return_value={"payload": {"result": "test-result"}})
        rpc_response.raise_for_status = MagicMock()

        mock_httpx_client.post.return_value = rpc_response

        # Pre-populate cache with valid token
        cache_key = self.get_cache_key(vista_client)
        vista_client.token_cache[cache_key] = valid_token

        # Make RPC call
        await vista_client.invoke_rpc(
            station="500",
            caller_duz="123",
            rpc_name="TEST_RPC",
        )

        # Should only have made the RPC call, not auth
        assert mock_httpx_client.post.call_count == 1
        assert "/rpc/invoke" in mock_httpx_client.post.call_args[0][0]

    async def test_token_caching_with_dynamic_ttl(
        self, vista_client, mock_httpx_client
    ):
        """Test that tokens are cached with TTL based on their expiry"""
        # Create a token that expires in 5 minutes
        exp_timestamp = int(
            (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()
        )
        token = create_test_jwt(exp_timestamp)

        # Mock the auth endpoint
        auth_response = AsyncMock()
        auth_response.status_code = 200
        auth_response.json = Mock(return_value={"data": {"token": token}})
        auth_response.raise_for_status = MagicMock()

        mock_httpx_client.post.return_value = auth_response

        # Get token
        result_token = await vista_client._get_jwt_token()

        # Check that token was cached
        cache_key = self.get_cache_key(vista_client)
        assert cache_key in vista_client.token_cache
        assert vista_client.token_cache[cache_key] == token

        # Cache TTL should be approximately 5 minutes minus buffer (30s)
        # We can't directly check TTL, but we can verify the token is there
        assert result_token == token

    @patch.dict("os.environ", {"VISTA_TOKEN_CACHE_ENABLED": "false"})
    async def test_caching_disabled(self, mock_httpx_client):
        """Test behavior when token caching is disabled"""
        # Create new client with caching disabled
        with patch(
            "src.api_clients.vista_client.httpx.AsyncClient"
        ) as mock_client_class:
            mock_client_class.return_value = mock_httpx_client

            client = VistaAPIClient(
                base_url="http://localhost:9000",
                api_key="test-key",
                auth_url="http://localhost:9000",
                timeout=30.0,
            )
            client.client = mock_httpx_client

            # Create tokens
            token1 = create_test_jwt(
                int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            )
            token2 = create_test_jwt(
                int((datetime.now(timezone.utc) + timedelta(hours=2)).timestamp())
            )

            # Mock auth responses
            auth_response1 = AsyncMock()
            auth_response1.status_code = 200
            auth_response1.json = Mock(return_value={"data": {"token": token1}})
            auth_response1.raise_for_status = MagicMock()

            auth_response2 = AsyncMock()
            auth_response2.status_code = 200
            auth_response2.json = Mock(return_value={"data": {"token": token2}})
            auth_response2.raise_for_status = MagicMock()

            # Mock RPC responses
            rpc_response = AsyncMock()
            rpc_response.status_code = 200
            rpc_response.json = Mock(return_value={"payload": {"result": "test"}})
            rpc_response.raise_for_status = MagicMock()

            mock_httpx_client.post.side_effect = [
                auth_response1,  # First auth
                rpc_response,  # First RPC
                auth_response2,  # Second auth (should not use cache)
                rpc_response,  # Second RPC
            ]

            # Make two RPC calls (disable response cache)
            await client.invoke_rpc("500", "123", "TEST_RPC", use_cache=False)
            await client.invoke_rpc("500", "123", "TEST_RPC", use_cache=False)

            # Should have made 2 auth calls (no caching)
            assert mock_httpx_client.post.call_count == 4

            auth_calls = [
                call
                for call in mock_httpx_client.post.call_args_list
                if "/auth/token" in call[0][0]
            ]
            assert len(auth_calls) == 2
