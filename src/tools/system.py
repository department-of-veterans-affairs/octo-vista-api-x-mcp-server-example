"""System tools for Vista API MCP Server"""

import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


def register_system_tools(server, vista_client):
    """Register system-related tools with the MCP server."""

    @server.tool()
    async def get_system_info() -> dict[str, Any]:
        """Get system information and status."""
        try:
            # Get local cache status if available
            cache_status = {}
            try:
                from src.services.cache.local_cache_manager import (
                    get_local_cache_status,
                )

                cache_status = get_local_cache_status()
            except ImportError:
                cache_status = {"error": "Local cache manager not available"}

            return {
                "status": "healthy",
                "server": "Vista API MCP Server",
                "cache": cache_status,
                "vista_client": {
                    "configured": bool(vista_client.base_url),
                    "base_url": vista_client.base_url or "not configured",
                    "auth_url": vista_client.auth_url or "not configured",
                },
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"status": "error", "error": str(e)}

    @server.tool()
    async def get_cache_status() -> dict[str, Any]:
        """Get detailed cache status and configuration."""
        try:
            from src.config import get_cache_config
            from src.services.cache.local_cache_manager import get_local_cache_status

            cache_config = get_cache_config()
            local_status = get_local_cache_status()

            return {
                "cache_config": cache_config,
                "local_status": local_status,
                "environment": {
                    "CACHE_BACKEND": os.getenv("CACHE_BACKEND", "not-set"),
                    "LOCAL_CACHE_MONITORING": os.getenv(
                        "LOCAL_CACHE_MONITORING", "false"
                    ),
                },
            }
        except ImportError:
            return {
                "error": "Cache services not available",
                "message": "Local cache manager or config not available",
            }
        except Exception as e:
            logger.error(f"Error getting cache status: {e}")
            return {"error": str(e)}

    @server.tool()
    async def restart_local_cache() -> dict[str, Any]:
        """Restart local cache infrastructure."""
        try:
            from src.services.cache.local_cache_manager import local_cache_manager

            # Stop existing containers
            compose_file = local_cache_manager.compose_file

            if compose_file.exists():
                result = subprocess.run(
                    f"docker-compose -f {compose_file} down",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    logger.info("Stopped existing local cache containers")
                else:
                    logger.warning(f"Failed to stop containers: {result.stderr}")

            # Reinitialize
            success = local_cache_manager.initialize_local_cache()

            return {
                "success": success,
                "message": (
                    "Local cache restarted"
                    if success
                    else "Failed to restart local cache"
                ),
                "status": local_cache_manager.get_cache_status(),
            }

        except ImportError:
            return {"error": "Local cache manager not available"}
        except Exception as e:
            logger.error(f"Error restarting local cache: {e}")
            return {"error": str(e)}
