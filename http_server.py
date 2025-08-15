"""Vista API MCP Server - Streamable HTTP Transport"""

import os
import sys

from dotenv import load_dotenv

# Import the MCP server instance from existing server
from server import mcp
from src.logging_config import get_logger, log_mcp_message

# Load environment variables
load_dotenv()

# Get MCP-compliant logger
logger = get_logger("mcp-server-http")


if __name__ == "__main__":
    # Server is already initialized via import from server.py
    log_mcp_message(mcp, "info", "Vista API MCP Server (HTTP mode)")

    # Get configuration from environment
    host = os.getenv("VISTA_MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("VISTA_MCP_HTTP_PORT", "8000"))

    # Additional configuration for enhanced transport support
    auth_header = os.getenv("VISTA_MCP_AUTH_HEADER")
    cors_origins = os.getenv("VISTA_MCP_CORS_ORIGINS")

    log_mcp_message(
        mcp,
        "info",
        f"Starting Streamable HTTP server. MCP endpoint: http://{host}:{port}/mcp. "
        f"Configure your client with: {{'transport': 'http', 'url': 'http://{host}:{port}/mcp'}}",
    )

    # Set environment variables for uvicorn
    os.environ["UVICORN_HOST"] = host
    os.environ["UVICORN_PORT"] = str(port)

    try:
        # Import uvicorn for HTTP transport
        import uvicorn

        # Modern Streamable HTTP transport
        log_mcp_message(
            mcp, "info", "Using Streamable HTTP transport and getting app..."
        )

        # Get the Streamable HTTP app
        app = mcp.streamable_http_app()

        # Add auth header if specified
        if auth_header:
            log_mcp_message(
                mcp,
                "info",
                f"Using authentication header: {auth_header.split('=')[0]}=***",
            )
            # Note: Auth implementation would need to be handled by the app

        # Add CORS configuration if specified
        if cors_origins:
            log_mcp_message(mcp, "info", f"CORS origins: {cors_origins}")
            # Note: CORS configuration would need to be implemented in FastMCP

        # Run the Streamable HTTP app with uvicorn
        log_mcp_message(mcp, "info", "Starting uvicorn server...")
        uvicorn.run(app, host=host, port=port, log_level="info")

    except KeyboardInterrupt:
        log_mcp_message(mcp, "info", "Server stopped by user")
    except Exception as e:
        log_mcp_message(
            mcp,
            "error",
            f"Server error: {e}. Streamable HTTP requires MCP SDK 1.10.0 or later. "
            f"Run 'uv add mcp>=1.10.0' to update.",
        )
        sys.exit(1)
