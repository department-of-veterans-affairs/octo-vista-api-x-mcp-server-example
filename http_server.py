"""Vista API MCP Server - HTTP/SSE Transport"""

import logging
import os
import sys
from typing import Literal, cast

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
    logger.info("Vista API MCP Server (HTTP/SSE mode)")

    # Get configuration from environment
    host = os.getenv("VISTA_MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("VISTA_MCP_HTTP_PORT", "8000"))
    transport = os.getenv("VISTA_MCP_TRANSPORT", "sse")  # 'sse' or 'streamable-http'

    logger.info(f"Starting {transport.upper()} server on {host}:{port}")

    # Set environment variables for uvicorn
    os.environ["UVICORN_HOST"] = host
    os.environ["UVICORN_PORT"] = str(port)

    try:
        # For SSE transport, we need to use the async method
        if transport == "sse":
            import uvicorn

            # Get the SSE app
            app = mcp.sse_app()

            # Run with uvicorn directly
            uvicorn.run(app, host=host, port=port, log_level="info")
        else:
            # Run with specified transport
            mcp.run(
                transport=cast(Literal["stdio", "sse", "streamable-http"], transport)
            )
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
