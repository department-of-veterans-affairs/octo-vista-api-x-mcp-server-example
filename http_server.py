"""Vista API MCP Server - Streamable HTTP Transport"""

import os
import sys

from dotenv import load_dotenv
from starlette.responses import JSONResponse
from starlette.routing import Route

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
    root_path = os.getenv("ROOT_PATH_PREFIX", "")

    # Additional configuration for enhanced transport support
    auth_header = os.getenv("VISTA_MCP_AUTH_HEADER")
    cors_origins = os.getenv("VISTA_MCP_CORS_ORIGINS")

    # Build the full MCP endpoint URL
    mcp_endpoint = f"http://{host}:{port}{root_path}/mcp"

    log_mcp_message(
        mcp,
        "info",
        f"Starting Streamable HTTP server. MCP endpoint: {mcp_endpoint}. "
        f"Root path prefix: '{root_path}'. "
        f"Configure your client with: {{'transport': 'http', 'url': '{mcp_endpoint}'}}",
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

        # Get the MCP Streamable HTTP app
        app = mcp.streamable_http_app()

        # Add health routes directly to the MCP app's router
        async def health_check(request):
            return JSONResponse({"status": "healthy", "service": "vista-mcp-server"})

        # Create base health routes
        health_routes = [
            Route("/", health_check),
            Route("/health", health_check),
        ]

        # Add prefixed routes if root_path is specified
        if root_path:
            log_mcp_message(mcp, "info", f"Adding prefixed routes for: {root_path}")

            # Copy the existing MCP route to the prefixed path
            mcp_routes_to_add = []
            for route in app.router.routes:
                if hasattr(route, "path") and route.path == "/mcp":
                    # Add a prefixed version of the MCP route
                    from starlette.routing import Route as StarletteRoute

                    # Safely get endpoint and methods from route
                    if hasattr(route, "endpoint"):
                        endpoint = route.endpoint
                        methods = (
                            route.methods
                            if hasattr(route, "methods")
                            else ["GET", "POST"]
                        )

                        prefixed_mcp_route = StarletteRoute(
                            f"{root_path}/mcp",
                            endpoint,
                            methods=methods,
                        )
                        mcp_routes_to_add.append(prefixed_mcp_route)
                        log_mcp_message(
                            mcp, "info", f"Added prefixed MCP route: {root_path}/mcp"
                        )

            # Add prefixed health routes
            prefixed_routes = [
                Route(f"{root_path}/", health_check),
                Route(f"{root_path}/health", health_check),
            ]
            health_routes.extend(prefixed_routes)
            health_routes.extend(mcp_routes_to_add)

        # Insert all routes at the beginning
        app.router.routes = health_routes + app.router.routes

        # Root path is handled by uvicorn, not the app directly
        if root_path:
            log_mcp_message(
                mcp, "info", f"Root path will be configured in uvicorn: {root_path}"
            )

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

        # Run the MCP app with uvicorn (FastMCP handles root_path internally)
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
