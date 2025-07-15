"""
Configuration management for Vista API X Mock Server
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # AWS Configuration
    aws_endpoint_url: str = "http://localhost:4566"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_default_region: str = "us-east-1"

    # DynamoDB Configuration
    dynamodb_table_name: str = "AUTH_APPLICATIONS_TABLE_NAME"

    # JWT Configuration
    jwt_private_key_path: str = "./keys/private_key.pem"
    jwt_public_key_path: str = "./keys/public_key.pem"
    jwt_issuer: str = "gov.va.octo.vista-api-x"
    jwt_audience: str = "gov.va.octo.vista-api-x"
    jwt_algorithm: str = "RS256"
    jwt_ttl_hours: float = 0.05  # 3 minutes in hours (matches staging)
    jwt_refresh_ttl_hours: int = 1  # 1 hour (60 minutes)
    jwt_clock_skew_seconds: int = 30

    # Application Configuration
    app_name: str = "Vista API X Mock Server"
    app_version: str = "2.1-mock"
    environment: str = "development"
    log_level: str = "INFO"
    server_port: int = 8080
    health_check_port: int = 9990

    # Mock Configuration
    enable_response_delay: bool = True
    min_response_delay_ms: int = 50
    max_response_delay_ms: int = 200
    error_injection_rate: float = 0.0

    # Test API Keys
    test_api_keys: list[str] = [
        "test-standard-key-123",
        "test-wildcard-key-456",
        "test-limited-key-789",
    ]

    # VistaLink Simulation
    vistalink_retry_attempts: int = 3
    vistalink_retry_delay_ms: int = 100
    vistalink_connection_timeout_ms: int = 5000

    # Request Limits
    max_request_size_mb: int = 10
    max_rpc_timeout_seconds: int = 60
    min_rpc_timeout_seconds: int = 10
    default_rpc_timeout_seconds: int = 15

    # CORS Configuration
    cors_allowed_origins: list[str] = ["*"]
    cors_allowed_methods: list[str] = ["GET", "POST", "OPTIONS"]
    cors_allowed_headers: list[str] = ["*"]

    # Special Headers
    ssoi_header_name: str = "X-OCTO-VISTA-API"
    bypass_auth_header: str = "X-UAAS-AUTH"
    bypass_auth_value: str = "auth-request"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"

    @property
    def jwt_private_key(self) -> bytes:
        """Load JWT private key from file"""
        return Path(self.jwt_private_key_path).read_bytes()

    @property
    def jwt_public_key(self) -> bytes:
        """Load JWT public key from file"""
        return Path(self.jwt_public_key_path).read_bytes()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
