"""Configuration for Vista MCP Server"""

import os

# Mock server configuration (fallback)
MOCK_SERVER_URL = "http://localhost:8888"
MOCK_API_KEY = "test-wildcard-key-456"

# Vista API configuration (from environment)
VISTA_API_BASE_URL = os.getenv("VISTA_API_BASE_URL", "")
VISTA_AUTH_URL = os.getenv("VISTA_AUTH_URL", "")
VISTA_API_KEY = os.getenv("VISTA_API_KEY", "")

# Default Vista configuration
DEFAULT_STATION = os.getenv("DEFAULT_STATION", "500")
DEFAULT_DUZ = os.getenv("DEFAULT_DUZ", "10000000219")

# Debug mode
DEBUG = os.getenv("VISTA_MCP_DEBUG", "false").lower() == "true"


def get_vista_config():
    """Get Vista configuration based on environment variables"""
    # Use production config if all required variables are set
    if VISTA_API_BASE_URL and VISTA_API_KEY:
        return {
            "base_url": VISTA_API_BASE_URL,
            "auth_url": VISTA_AUTH_URL or VISTA_API_BASE_URL,
            "api_key": VISTA_API_KEY,
            "mode": "production",
        }
    else:
        # Fall back to mock server
        return {
            "base_url": MOCK_SERVER_URL,
            "auth_url": MOCK_SERVER_URL,
            "api_key": MOCK_API_KEY,
            "mode": "mock",
        }
