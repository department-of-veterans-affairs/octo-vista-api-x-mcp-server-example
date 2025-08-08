"""Vista API MCP Server - Main entry point"""

import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.config import get_vista_config
from src.tools.patient import register_patient_tools
from src.tools.system import register_system_tools

# Import from src directory
from src.vista.client import VistaAPIClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not os.getenv("VISTA_MCP_DEBUG") else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize MCP server (global for mcp dev)
mcp = FastMCP(
    name="VistA API X MCP Server",
)

# Store as 'server' for mcp dev compatibility
server = mcp


def initialize_server():
    """Initialize the server components"""
    logger.info("Initializing Vista API MCP Server...")

    # Create Vista client
    try:
        config = get_vista_config()

        logger.info(f"🔧 Vista mode: {config['mode'].upper()}")
        logger.info(f"Auth endpoint: {config['auth_url']}")
        logger.info(f"API endpoint: {config['base_url']}")

        vista_client = VistaAPIClient(
            base_url=config["base_url"],
            api_key=config["api_key"],
            auth_url=config["auth_url"],
            timeout=30.0,
        )
    except Exception as e:
        logger.error(f"Failed to create Vista client: {e}")
        raise

    # Register all tools
    logger.info("Registering tools...")
    register_patient_tools(mcp, vista_client)
    register_system_tools(mcp, vista_client)

    # # Register resources
    # logger.info("Registering resources...")
    # register_resources(mcp)

    # # Register prompts
    # logger.info("Registering prompts...")
    # register_prompts(mcp)

    logger.info("Vista API MCP Server initialized successfully")


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
