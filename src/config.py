"""Configuration for Vista MCP Server"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    """Get Vista configuration from environment variables only"""
    # Always use exactly what's in the .env file
    # No fallbacks - if values are wrong, connections will fail
    return {
        "base_url": VISTA_API_BASE_URL,
        "auth_url": VISTA_AUTH_URL or VISTA_API_BASE_URL,
        "api_key": VISTA_API_KEY,
        "mode": "production" if VISTA_API_BASE_URL else "unconfigured",
    }
