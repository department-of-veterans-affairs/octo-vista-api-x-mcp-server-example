"""Local Cache Manager for Vista API MCP Server

This module manages local cache infrastructure startup and health checks.
"""

import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalCacheManager:
    """Manages local cache infrastructure for development."""

    def __init__(self):
        self.redis_running = False
        self.redis_healthy = False
        self.compose_file = (
            Path(__file__).parent.parent.parent.parent / "docker-compose.local.yml"
        )

    def should_start_local_cache(self) -> bool:
        """Determine if local cache should be started based on environment."""
        cache_backend = os.getenv("CACHE_BACKEND", "").lower()
        return cache_backend in ["local-dev", "local-dev-redis"]

    def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                "docker info", shell=True, capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def check_docker_compose_available(self) -> bool:
        """Check if docker-compose is available."""
        try:
            result = subprocess.run(
                "docker-compose --version",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_redis_running(self) -> bool:
        """Check if Redis container is already running."""
        try:
            result = subprocess.run(
                "docker ps --format '{{.Names}}' | grep -q vista-local-redis",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def wait_for_redis_healthy(self, timeout: int = 30) -> bool:
        """Wait for Redis container to be healthy."""
        logger.info("Waiting for Redis to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    "docker ps --format '{{.Names}} {{.Status}}' | grep vista-local-redis | grep -q healthy",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    logger.info("Redis is ready!")
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

            time.sleep(1)

        logger.warning("Redis failed to start within 30 seconds")
        return False

    def start_redis(self) -> bool:
        """Start Redis container."""
        # First check if Redis is already running on port 6379
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
            r.ping()
            logger.info(
                "Redis is already running on port 6379, skipping local cache start"
            )
            return True
        except Exception:
            pass  # Redis not available, continue with startup

        if not self.compose_file.exists():
            logger.warning(f"Docker compose file not found: {self.compose_file}")
            return False

        logger.info("Starting Redis container...")
        try:
            result = subprocess.run(
                f"docker-compose -f {self.compose_file} up -d redis-local",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # Check if it's a port conflict error and Redis is actually available
                if "port is already allocated" in result.stderr:
                    logger.info(
                        "Port 6379 already in use, checking if Redis is accessible..."
                    )
                    try:
                        import redis

                        r = redis.Redis(
                            host="localhost", port=6379, socket_connect_timeout=1
                        )
                        r.ping()
                        logger.info(
                            "Redis is accessible on port 6379, using existing instance"
                        )
                        return True
                    except Exception:
                        logger.error(
                            f"Port 6379 is in use but Redis is not accessible: {result.stderr}"
                        )
                        return False

                logger.error(f"Failed to start Redis: {result.stderr}")
                return False

            return self.wait_for_redis_healthy()

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Error starting Redis: {e}")
            return False

    def start_monitoring_tools(self) -> bool:
        """Start optional monitoring tools if requested."""
        if os.getenv("LOCAL_CACHE_MONITORING", "false").lower() != "true":
            return True

        logger.info("Starting monitoring tools...")
        try:
            result = subprocess.run(
                f"docker-compose -f {self.compose_file} up -d redis-commander redis-insight",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info("Monitoring tools started:")
                logger.info("   - Redis Commander: http://localhost:8081")
                logger.info("   - Redis Insight: http://localhost:8001")
                return True
            else:
                logger.warning(f"Failed to start monitoring tools: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Error starting monitoring tools: {e}")
            return False

    def initialize_local_cache(self) -> bool:
        """Initialize local cache infrastructure if needed."""
        if not self.should_start_local_cache():
            logger.debug("Local cache not requested, skipping initialization")
            return True

        logger.info("Initializing local cache infrastructure...")

        # Check if Docker is available
        if not self.check_docker_available():
            logger.warning(
                "Docker not available, local cache will use in-memory fallback"
            )
            return True

        if not self.check_docker_compose_available():
            logger.warning(
                "docker-compose not available, local cache will use in-memory fallback"
            )
            return True

        # Check if Redis is already running
        if self.is_redis_running():
            logger.info("Redis is already running")
            self.redis_running = True
            self.redis_healthy = True
            return True

        # Start Redis
        if self.start_redis():
            self.redis_running = True
            self.redis_healthy = True

            # Start monitoring tools if requested
            self.start_monitoring_tools()

            logger.info("Local cache infrastructure initialized successfully")
            return True
        else:
            logger.warning(
                "Failed to start Redis, local cache will use in-memory fallback"
            )
            return False

    def get_cache_status(self) -> dict:
        """Get current cache infrastructure status."""
        return {
            "local_cache_enabled": self.should_start_local_cache(),
            "docker_available": self.check_docker_available(),
            "docker_compose_available": self.check_docker_compose_available(),
            "redis_running": self.redis_running,
            "redis_healthy": self.redis_healthy,
            "compose_file_exists": self.compose_file.exists(),
            "cache_backend": os.getenv("CACHE_BACKEND", "not-set"),
            "monitoring_enabled": os.getenv("LOCAL_CACHE_MONITORING", "false").lower()
            == "true",
        }


# Global instance for server integration
local_cache_manager = LocalCacheManager()


def initialize_local_cache_for_server() -> bool:
    """Initialize local cache infrastructure for the server.

    This function should be called during server startup.
    """
    return local_cache_manager.initialize_local_cache()


def get_local_cache_status() -> dict:
    """Get local cache status for server monitoring."""
    return local_cache_manager.get_cache_status()
