"""Main entry point for Vista API MCP Server"""

from .server import mcp

# The server is already initialized when imported
if __name__ == "__main__":
    mcp.run()