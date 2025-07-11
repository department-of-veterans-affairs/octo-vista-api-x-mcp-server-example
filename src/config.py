"""Configuration for Vista MCP Server"""

import os
from typing import Literal

# Server mode - controls which Vista API to connect to
VISTA_MODE: Literal["mock", "production", "auto"] = os.getenv(
    "VISTA_MODE", "mock"
).lower()  # type: ignore

# Mock server configuration
MOCK_SERVER_URL = "http://localhost:8080"
MOCK_API_KEY = "test-wildcard-key-456"

# Production configuration (from environment)
PROD_BASE_URL = os.getenv("VISTA_API_BASE_URL", "")
PROD_AUTH_URL = os.getenv("VISTA_AUTH_URL", "")
PROD_API_KEY = os.getenv("VISTA_API_KEY", "")

# Default Vista configuration
DEFAULT_STATION = os.getenv("DEFAULT_STATION", "500")
DEFAULT_DUZ = os.getenv("DEFAULT_DUZ", "10000000219")

# Debug mode
DEBUG = os.getenv("VISTA_MCP_DEBUG", "false").lower() == "true"


def get_vista_config():
    """Get Vista configuration based on mode"""
    if VISTA_MODE == "mock":
        return {
            "base_url": MOCK_SERVER_URL,
            "auth_url": MOCK_SERVER_URL,
            "api_key": MOCK_API_KEY,
            "mode": "mock",
        }
    elif VISTA_MODE == "production" and PROD_BASE_URL and PROD_API_KEY:
        return {
            "base_url": PROD_BASE_URL,
            "auth_url": PROD_AUTH_URL or PROD_BASE_URL,
            "api_key": PROD_API_KEY,
            "mode": "production",
        }
    else:
        # Auto mode: use mock if no production config
        if PROD_BASE_URL and PROD_API_KEY:
            return {
                "base_url": PROD_BASE_URL,
                "auth_url": PROD_AUTH_URL or PROD_BASE_URL,
                "api_key": PROD_API_KEY,
                "mode": "production",
            }
        else:
            return {
                "base_url": MOCK_SERVER_URL,
                "auth_url": MOCK_SERVER_URL,
                "api_key": MOCK_API_KEY,
                "mode": "mock",
            }
