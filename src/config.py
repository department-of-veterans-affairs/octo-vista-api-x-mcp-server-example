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

# AWS Caching Configuration
AWS_CACHE_BACKEND = os.getenv("AWS_CACHE_BACKEND", "elasticache").lower()
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "elasticache").lower()

# ElastiCache for Redis Configuration
ELASTICACHE_ENDPOINT = os.getenv("ELASTICACHE_ENDPOINT")
ELASTICACHE_PORT = int(os.getenv("ELASTICACHE_PORT", "6379"))
ELASTICACHE_AUTH_TOKEN = os.getenv("ELASTICACHE_AUTH_TOKEN")

# DynamoDB Accelerator (DAX) Configuration
DAX_ENDPOINT = os.getenv("DAX_ENDPOINT")
DAX_TABLE_NAME = os.getenv("DAX_TABLE_NAME", "vista_cache")

# Redis Configuration (fallback)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# AWS General Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CACHE_KEY_PREFIX = os.getenv("CACHE_KEY_PREFIX", "mcp:")

# Cache TTL Configuration (Updated)
PATIENT_CACHE_TTL_MINUTES = int(
    os.getenv("PATIENT_CACHE_TTL_MINUTES", "20")
)  # Increased from 10
TOKEN_CACHE_TTL_MINUTES = int(
    os.getenv("TOKEN_CACHE_TTL_MINUTES", "55")
)  # Keep current
RESPONSE_CACHE_TTL_MINUTES = int(
    os.getenv("RESPONSE_CACHE_TTL_MINUTES", "10")
)  # Increased from 5

# Multi-tier Cache Configuration
MULTI_TIER_WRITE_THROUGH = (
    os.getenv("MULTI_TIER_WRITE_THROUGH", "true").lower() == "true"
)
MULTI_TIER_READ_THROUGH = os.getenv("MULTI_TIER_READ_THROUGH", "true").lower() == "true"


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


def get_cache_config():
    """Get cache configuration from environment variables"""
    return {
        "backend_type": CACHE_BACKEND,
        "aws_backend": AWS_CACHE_BACKEND,
        "elasticache": {
            "endpoint": ELASTICACHE_ENDPOINT,
            "port": ELASTICACHE_PORT,
            "auth_token": ELASTICACHE_AUTH_TOKEN,
            "region": AWS_REGION,
        },
        "dax": {
            "endpoint": DAX_ENDPOINT,
            "table_name": DAX_TABLE_NAME,
            "region": AWS_REGION,
        },
        "redis": {
            "url": REDIS_URL,
        },
        "ttl": {
            "patient_minutes": PATIENT_CACHE_TTL_MINUTES,
            "token_minutes": TOKEN_CACHE_TTL_MINUTES,
            "response_minutes": RESPONSE_CACHE_TTL_MINUTES,
        },
        "multi_tier": {
            "write_through": MULTI_TIER_WRITE_THROUGH,
            "read_through": MULTI_TIER_READ_THROUGH,
        },
        "general": {
            "key_prefix": CACHE_KEY_PREFIX,
            "aws_region": AWS_REGION,
        },
    }


def is_aws_cache_enabled():
    """Check if AWS caching is enabled"""
    return ELASTICACHE_ENDPOINT is not None or DAX_ENDPOINT is not None


def get_cache_backend_priority():
    """Get cache backend priority order"""
    backend_priorities = {
        "multi-tier": ["elasticache", "dax", "redis"],
        "elasticache": ["elasticache", "redis"],
        "dax": ["dax", "redis"],
        "redis": ["redis"],
    }

    return backend_priorities.get(
        CACHE_BACKEND, ["elasticache", "redis"]
    )  # Default fallback
