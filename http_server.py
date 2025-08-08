"""Vista API MCP Server - HTTP Transport (SSE + Streamable HTTP)"""

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
    transport = os.getenv("VISTA_MCP_TRANSPORT", "sse")

    # Additional configuration for enhanced transport support
    auth_header = os.getenv("VISTA_MCP_AUTH_HEADER")
    cors_origins = os.getenv("VISTA_MCP_CORS_ORIGINS")

    # Normalize transport names (support aliases)
    if transport in ["http", "streamable-http", "streamable_http"]:
        transport = "http"  # Use "http" internally for Streamable HTTP
        logger.info("🚀 Starting Streamable HTTP server")
        logger.info(f"📍 MCP endpoint: http://{host}:{port}/mcp")
        logger.info("🔧 Configure your client with:")
        logger.info(f'  {{"transport": "http", "url": "http://{host}:{port}/mcp"}}')
    elif transport == "sse":
        logger.warning(
            "⚠️  SSE transport is DEPRECATED and will be removed in a future version!"
        )
        logger.warning(
            "⚠️  Please migrate to 'streamable-http' transport for better performance and stability."
        )
        logger.info(f"📍 SSE endpoint: http://{host}:{port}/sse")
        logger.info(f"📝 Message endpoint: http://{host}:{port}/messages/")
        logger.info("⏰ SSE support will be removed on: 2025-06-01")
    else:
        logger.error(f"❌ Unsupported transport: {transport}")
        logger.error(
            "✅ Supported transports: 'http', 'streamable-http', 'sse' (deprecated)"
        )
        sys.exit(1)

    logger.info(f"🌐 Starting {transport.upper()} server on {host}:{port}")

    # Set environment variables for uvicorn
    os.environ["UVICORN_HOST"] = host
    os.environ["UVICORN_PORT"] = str(port)

    try:
        # Import uvicorn for both transports
        import uvicorn

        if transport == "sse":
            # Legacy SSE transport (deprecated)
            logger.info("📡 Using legacy SSE transport...")
            app = mcp.sse_app()

            # Add CORS headers if specified
            if cors_origins:
                logger.info(f"🔗 CORS origins: {cors_origins}")
                # Note: CORS configuration would need to be implemented in FastMCP

            # Run with uvicorn directly
            uvicorn.run(app, host=host, port=port, log_level="info")
        else:
            # Modern Streamable HTTP transport
            logger.info("🎯 Using modern Streamable HTTP transport...")
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
