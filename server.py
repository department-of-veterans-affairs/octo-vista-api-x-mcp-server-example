"""Vista API MCP Server - Main entry point"""

import os
import sys

from dotenv import load_dotenv
from fastmcp import FastMCP

from src.config import get_vista_config
from src.logging_config import get_logger, log_mcp_message
from src.middleware import register_middleware
from src.tools.patient import register_patient_tools
from src.tools.system import register_system_tools

# Import from src directory
from src.vista.client import VistaAPIClient

# Load environment variables
load_dotenv()

# Get MCP-compliant logger
logger = get_logger("mcp-server")

# Initialize MCP server (global for mcp dev)
mcp = FastMCP(
    name="VistA API X MCP Server",
)

# Store as 'server' for mcp dev compatibility
server = mcp


def initialize_server():
    """Initialize the server components"""
    log_mcp_message(mcp, "info", "Initializing Vista API MCP Server...")

    # Initialize local cache infrastructure if needed
    try:
        from src.services.cache.local_cache_manager import (
            initialize_local_cache_for_server,
        )

        cache_init_success = initialize_local_cache_for_server()
        if cache_init_success:
            log_mcp_message(mcp, "info", "Local cache infrastructure initialized")
        else:
            log_mcp_message(
                mcp, "warning", "Local cache infrastructure failed, using fallback"
            )
    except ImportError:
        log_mcp_message(
            mcp,
            "debug",
            "Local cache manager not available, skipping cache initialization",
        )
    except Exception as e:
        log_mcp_message(mcp, "warning", f"Local cache initialization error: {e}")

    # Create Vista client
    try:
        config = get_vista_config()

        log_mcp_message(
            mcp,
            "info",
            f"Vista mode: {config['mode'].upper()}, Auth endpoint: {config['auth_url']}, "
            f"API endpoint: {config['base_url']}",
        )

        vista_client = VistaAPIClient(
            base_url=config["base_url"],
            api_key=config["api_key"],
            auth_url=config["auth_url"],
            timeout=30.0,
        )
    except Exception as e:
        logger.error(f"Failed to create Vista client: {e}")
        raise

    # Register middleware
    register_middleware(mcp)
    print("Middleware registered")

    # Register all tools
    log_mcp_message(mcp, "info", "Registering tools...")
    register_patient_tools(mcp, vista_client)
    register_system_tools(mcp, vista_client)

    log_mcp_message(mcp, "info", "Vista API MCP Server initialized successfully")


# Initialize on import for mcp dev
initialize_server()


if __name__ == "__main__":
    # Check if we should run with streamable HTTP transport
    transport = os.getenv("VISTA_MCP_TRANSPORT", "stdio")

    if transport in ["http", "streamable-http", "streamable_http"]:
        # Run with streamable HTTP transport
        try:
            mcp.run(transport="streamable-http")
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"\nServer error: {e}")
            sys.exit(1)
    else:
        # Run the server with stdio transport (for mcp dev)
        try:
            mcp.run()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"\nServer error: {e}")
            sys.exit(1)
