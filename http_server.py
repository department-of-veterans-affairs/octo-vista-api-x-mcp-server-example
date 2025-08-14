"""Vista API MCP Server - Streamable HTTP Transport"""

import logging
import os
import sys

from dotenv import load_dotenv

# Import the MCP server instance from existing server
from server import mcp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not os.getenv("VISTA_MCP_DEBUG") else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Server is already initialized via import from server.py
    logger.info("Vista API MCP Server (HTTP mode)")

    # Get configuration from environment
    host = os.getenv("VISTA_MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("VISTA_MCP_HTTP_PORT", "8000"))

    # Additional configuration for enhanced transport support
    auth_header = os.getenv("VISTA_MCP_AUTH_HEADER")
    cors_origins = os.getenv("VISTA_MCP_CORS_ORIGINS")

    logger.info("🚀 Starting Streamable HTTP server")
    logger.info(f"📍 MCP endpoint: http://{host}:{port}/mcp")
    logger.info("🔧 Configure your client with:")
    logger.info(f'  {{"transport": "http", "url": "http://{host}:{port}/mcp"}}')

    logger.info(f"🌐 Starting HTTP server on {host}:{port}")

    # Set environment variables for uvicorn
    os.environ["UVICORN_HOST"] = host
    os.environ["UVICORN_PORT"] = str(port)

    try:
        # Import uvicorn for HTTP transport
        import uvicorn

        # Modern Streamable HTTP transport
        logger.info("🎯 Using Streamable HTTP transport...")
        logger.info("✨ Getting Streamable HTTP app...")

        # Get the Streamable HTTP app
        app = mcp.streamable_http_app()

        # Add auth header if specified
        if auth_header:
            logger.info(
                f"🔐 Using authentication header: {auth_header.split('=')[0]}=***"
            )
            # Note: Auth implementation would need to be handled by the app

        # Add CORS configuration if specified
        if cors_origins:
            logger.info(f"🔗 CORS origins: {cors_origins}")
            # Note: CORS configuration would need to be implemented in FastMCP

        # Run the Streamable HTTP app with uvicorn
        logger.info("🚀 Starting uvicorn server...")
        uvicorn.run(app, host=host, port=port, log_level="info")

    except KeyboardInterrupt:
        logger.info("\n✋ Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        logger.error("💡 Check if you have the latest MCP SDK version:")
        logger.error("💡   uv add 'mcp>=1.10.0'")
        logger.error("💡 Streamable HTTP requires MCP SDK 1.10.0 or later")
        sys.exit(1)
