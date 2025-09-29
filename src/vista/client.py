"""Vista API X client wrapper with authentication and caching"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx
from cachetools import TTLCache

from ..services.cache.base import CacheBackend
from ..services.cache.factory import CacheFactory
from .auth.jwt import get_token_ttl_seconds, has_token_expired
from .base import BaseVistaClient, VistaAPIError

logger = logging.getLogger(__name__)


class VistaAPIClient(BaseVistaClient):
    """Client for interacting with Vista API X"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        auth_url: str,
        timeout: float = 30.0,
        token_cache_ttl: int = 3300,  # 55 minutes
        response_cache_ttl: int = 300,  # 5 minutes
        response_cache_backend: CacheBackend | None = None,
    ):
        """
        Initialize Vista API client

        Args:
            base_url: Vista API X base URL for RPC invocations
            api_key: API key for authentication
            auth_url: Auth service URL for JWT token generation
            timeout: Request timeout in seconds
            token_cache_ttl: JWT token cache TTL in seconds
            response_cache_ttl: Response cache TTL in seconds
            response_cache_backend: Optional cache backend for responses (uses Redis if available)
        """
        super().__init__(timeout)
        self.base_url = base_url.rstrip("/")
        self.auth_url = auth_url.rstrip("/")
        self.api_key = api_key

        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=timeout, verify=False)

        # Initialize caches
        self.token_cache: TTLCache[str, str] = TTLCache(maxsize=10, ttl=token_cache_ttl)

        self.response_cache_backend = response_cache_backend
        self.response_cache_ttl = timedelta(seconds=response_cache_ttl)

        # Use TTLCache as fallback if no backend provided
        self._ttl_response_cache: TTLCache[str, Any] | None = None
        if self.response_cache_backend is None:
            self._ttl_response_cache = TTLCache(maxsize=1000, ttl=response_cache_ttl)
            logger.info("Using in-memory TTLCache for response caching")
        else:
            logger.info(
                f"Using {type(self.response_cache_backend).__name__} for response caching"
            )

        self._token: str | None = None
        self._token_expiry: datetime | None = None

        # Token refresh configuration
        self._token_refresh_buffer_seconds = int(
            os.getenv("VISTA_TOKEN_REFRESH_BUFFER_SECONDS", "30")
        )
        self._token_cache_enabled = (
            os.getenv("VISTA_TOKEN_CACHE_ENABLED", "true").lower() == "true"
        )

        # Track if we need to initialize async cache
        self._cache_initialized = False

    async def _get_jwt_token(self) -> str:
        """Get or refresh JWT token"""
        cache_key = f"token_{self.api_key}"

        # Check cache first if enabled
        if self._token_cache_enabled and cache_key in self.token_cache:
            cached_token = self.token_cache[cache_key]
            # Validate cached token isn't expired
            if not has_token_expired(cached_token, self._token_refresh_buffer_seconds):
                logger.debug("Using cached JWT token")
                return cached_token
            else:
                logger.info("Cached token expired or expiring soon, refreshing")
                del self.token_cache[cache_key]

        logger.info("Obtaining new JWT token")

        try:
            response = await self.client.post(
                f"{self.auth_url}/vista-api-x/auth/token",
                json={"key": self.api_key},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            data = response.json()
            token = data["data"]["token"]

            if not token:
                raise VistaAPIError(
                    error_type="AuthenticationError",
                    error_code="NoToken",
                    message="No token received from authentication service",
                    status_code=response.status_code,
                )

            # Cache the token if caching is enabled
            if self._token_cache_enabled:
                # Simply store the token - the TTLCache was already initialized with a default TTL
                # We'll check expiry when retrieving from cache
                self.token_cache[cache_key] = token

                # Log the actual token lifetime for debugging
                token_ttl = get_token_ttl_seconds(token)
                logger.info(
                    f"JWT token obtained and cached (expires in {token_ttl:.0f}s)"
                )
            else:
                logger.info("JWT token obtained (caching disabled)")

            return token

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to obtain JWT token: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Error obtaining JWT token: {str(e)}")
            raise

    async def _ensure_valid_token(self) -> str:
        """
        Ensure we have a valid (non-expired) JWT token.

        Returns:
            Valid JWT token
        """
        cache_key = f"token_{self.api_key}"

        # Check if we have a cached token and if it's still valid
        if self._token_cache_enabled and cache_key in self.token_cache:
            token = self.token_cache[cache_key]
            if not has_token_expired(token, self._token_refresh_buffer_seconds):
                return token
            else:
                logger.info("Token expired or expiring soon, refreshing proactively")
                del self.token_cache[cache_key]

        # Get a fresh token
        return await self._get_jwt_token()

    async def invoke_rpc(
        self,
        station: str,
        caller_duz: str,
        rpc_name: str,
        context: str = "OR CPRS GUI CHART",
        parameters: list[dict[str, Any]] | None = None,
        json_result: bool = False,
        use_cache: bool = True,
        client_jwt: str | None = None,
    ) -> Any:
        """
        Invoke a Vista RPC

        Args:
            station: Vista station number
            caller_duz: DUZ of the calling user
            rpc_name: Name of the RPC to invoke
            context: RPC context (default: OR CPRS GUI CHART)
            parameters: RPC parameters
            json_result: Whether to request JSON response
            use_cache: Whether to use response cache
            client_jwt: JWT token from client (when USE_CLIENT_JWT=true)

        Returns:
            RPC response (string or dict depending on RPC and json_result)
        """
        # Initialize cache backend if needed (first RPC call)
        if not self._cache_initialized:
            await self._ensure_cache_initialized()

        # Create cache key using deterministic hash
        # Use MD5 for speed (not for security, just for cache key generation)
        param_hash = hashlib.md5(
            json.dumps(parameters, sort_keys=True).encode()
        ).hexdigest()[
            :16
        ]  # Use first 16 chars of hash for brevity
        cache_key = f"{station}:{caller_duz}:{rpc_name}:{param_hash}"

        # Check cache if enabled
        if use_cache:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response is not None:
                logger.debug(f"Using cached response for {rpc_name}")
                return cached_response

        # Determine which JWT to use based on configuration
        if client_jwt:
            # USE_CLIENT_JWT mode: use client-provided JWT
            token = client_jwt
            logger.info(
                f"CLIENT_JWT_MODE: {json.dumps({'using_client_jwt': True, 'jwt_length': len(token)})}"
            )
        else:
            # Service-to-service auth: fetch JWT using API key
            token = await self._ensure_valid_token()
            logger.info(
                f"SERVICE_AUTH_MODE: {json.dumps({'using_client_jwt': False, 'fetching_jwt': True})}"
            )

        # Build request payload
        payload: dict[str, Any] = {
            "rpc": rpc_name,
            "context": context,
        }

        if json_result:
            payload["jsonResult"] = True

        if parameters:
            payload["parameters"] = parameters

        # Build URL
        url = f"{self.base_url}/vista-api-x/vista-sites/{station}/users/{caller_duz}/rpc/invoke"

        # Build headers based on JWT mode
        if client_jwt:
            # USE_CLIENT_JWT mode: JWT in Authorization, API key in X-OCTO-VISTA-API
            headers = {
                "Authorization": f"Bearer {token}",
                "X-OCTO-VISTA-API": self.api_key,
                "Content-Type": "application/json",
            }
        else:
            # Service-to-service auth: JWT in Authorization only
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

        logger.debug(f"Invoking RPC: {rpc_name} at station {station}")

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            # Extract result
            data = response.json()
            logger.debug(
                f"RPC_RESPONSE_DATA: {json.dumps({'has_payload': 'payload' in data, 'data_keys': list(data.keys()) if isinstance(data, dict) else 'not_dict'})}"
            )

            # Vista API X returns the result in different formats
            if "payload" in data:
                result = data["payload"]
                # Some RPCs return result wrapped in another layer
                if isinstance(result, dict) and "result" in result:
                    result = result["result"]
            else:
                result = data

            # Cache successful response
            if use_cache:
                await self._set_cached_response(cache_key, result)

            logger.debug(f"RPC {rpc_name} completed successfully")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"RPC invocation failed: {e.response.status_code} - {e.response.text}"
            )
            # Parse error response
            try:
                error_data = e.response.json()
                raise VistaAPIError(
                    error_type=error_data.get("errorType", "Unknown"),
                    error_code=error_data.get("errorCode", ""),
                    message=error_data.get("message", str(e)),
                    status_code=e.response.status_code,
                )
            except Exception:
                raise VistaAPIError(
                    error_type="HTTPError",
                    error_code=str(e.response.status_code),
                    message=str(e),
                    status_code=e.response.status_code,
                ) from e
        except Exception as e:
            logger.error(f"Error invoking RPC {rpc_name}: {str(e)}")
            raise

    async def _ensure_cache_initialized(self):
        """Initialize cache backend if needed (lazy initialization for async)"""
        if self._cache_initialized:
            return

        # If no backend was provided and CACHE_BACKEND env var is set to redis
        if (
            self.response_cache_backend is None
            and os.getenv("CACHE_BACKEND") == "redis"
        ):
            try:
                logger.info(
                    "CACHE_BACKEND=redis detected, attempting to use Redis for response caching"
                )
                self.response_cache_backend = await CacheFactory.create_backend()
                self._ttl_response_cache = None  # Clear TTL cache if we got Redis
                logger.info(
                    f"Successfully initialized {type(self.response_cache_backend).__name__} for response caching"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Redis cache backend: {e}, falling back to in-memory cache"
                )
                # Keep using TTL cache as fallback

        self._cache_initialized = True

    async def _get_cached_response(self, cache_key: str) -> Any | None:
        """Get response from cache (handles both TTLCache and CacheBackend)"""
        if self.response_cache_backend:
            # Using CacheBackend (Redis/etc)
            try:
                cached_value = await self.response_cache_backend.get(cache_key)
                if cached_value:
                    # Deserialize if it's a string (Redis stores as string)
                    if isinstance(cached_value, str):
                        try:
                            return json.loads(cached_value)
                        except json.JSONDecodeError:
                            return cached_value
                    return cached_value
            except Exception as e:
                logger.warning(f"Error getting cached response: {e}")
                return None
        elif self._ttl_response_cache:
            # Using in-memory TTLCache
            return self._ttl_response_cache.get(cache_key)
        return None

    async def _set_cached_response(self, cache_key: str, value: Any):
        """Set response in cache (handles both TTLCache and CacheBackend)"""
        if self.response_cache_backend:
            # Using CacheBackend (Redis/etc)
            try:
                # Serialize to JSON string for Redis
                cache_value = json.dumps(value) if not isinstance(value, str) else value
                await self.response_cache_backend.set(
                    cache_key, cache_value, ttl=self.response_cache_ttl
                )
                logger.debug(
                    f"Cached response in {type(self.response_cache_backend).__name__}"
                )
            except Exception as e:
                logger.warning(f"Error caching response: {e}")
        elif self._ttl_response_cache:
            # Using in-memory TTLCache
            self._ttl_response_cache[cache_key] = value
            logger.debug("Cached response in TTLCache")

    async def close(self):
        """Close the HTTP client and cache connections"""
        await self.client.aclose()
        if self.response_cache_backend:
            try:
                await self.response_cache_backend.close()
            except Exception as e:
                logger.warning(f"Error closing cache backend: {e}")
