# Vista API MCP Server

MCP (Model Context Protocol) server that provides natural language access to VistA healthcare data through Vista API X.

## Quick Start

### Option 1: stdio Transport (Local Development)
```bash
# Traditional stdio mode with MCP inspector
mise run dev-with-mock
```

### Option 2: SSE Transport (Remote Access)
```bash
# SSE server mode accessible via URL
mise run dev-sse-with-mock
```

Then connect via URL: `http://localhost:8000/sse`

## Features

- **20+ VistA Tools**: Patient search, clinical data, administrative functions
- **Mock Server Included**: Full Vista API X mock for development
- **Dual Transport**: stdio for local dev, SSE for remote access
- **LLM Client Ready**: Works with any MCP-compatible client
- **Type-Safe**: Full type hints and validation
- **Production Ready**: Docker support for easy deployment

## Client Setup

Connect the Vista API MCP Server to your favorite LLM:

- **[Claude Desktop](docs/CLIENT_SETUP.md#claude-desktop)** - Native MCP support
- **[Cursor IDE](docs/CLIENT_SETUP.md#cursor)** - AI-powered code editor
- **[VS Code + Cline](docs/CLIENT_SETUP.md#vs-code-cline-extension)** - Popular IDE with MCP
- **[Other Clients](docs/CLIENT_SETUP.md#custom-mcp-clients)** - Zed, custom implementations

### Quick Setup for Claude Desktop

```bash
# Automatic setup script
python scripts/setup_claude_desktop.py
```

Example config files are included:
- `claude_desktop_config.example.json` - Claude Desktop template
- `.cursorrules.example` - Cursor IDE template

## Docker Deployment

### Production
```bash
# Set your production Vista API endpoint
export VISTA_API_BASE_URL=https://your-vista-api.va.gov
export VISTA_API_KEY=your-production-api-key

# Run the SSE server
docker-compose up -d
```

### Local Development with Mock
```bash
# Run with the included development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This automatically connects to the Vista API X mock server if it's running.

## Configuration

The server automatically detects whether to use production Vista API or the mock server based on environment variables:

```bash
# In your .env file:
VISTA_API_BASE_URL=https://your-vista-api.com  # Production API URL
VISTA_AUTH_URL=https://your-vista-auth.com     # Auth service URL (optional, defaults to API URL)
VISTA_API_KEY=your-api-key                     # Your Vista API key
```

- If all required variables are set, the server uses production Vista API
- If any are missing, it falls back to the mock server at localhost:8888

To verify your configuration:
```bash
python scripts/test_config.py
```

## Documentation

- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Client Setup](docs/CLIENT_SETUP.md) - Connect to Claude, Cursor, and other clients
- [Transport Modes](docs/TRANSPORTS.md) - stdio vs HTTP/SSE transports
- [Tools Reference](docs/TOOLS.md) - All available MCP tools
- [Example Prompts](docs/PROMPTS.md) - Sample queries and workflows
- [Testing Guide](docs/TESTING.md) - Test data and testing strategies
- [Development](docs/DEVELOPMENT.md) - Contributing and extending
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Deployment](docs/DEPLOYMENT.md) - Production deployment guide

## Example Usage

Once configured in your LLM client:

```
You: "Search for patients with last name ANDERSON"
Assistant: I'll search for patients with the last name Anderson...
[Uses search_patients tool]

You: "Show medications for patient 100022"
Assistant: I'll retrieve the medications for patient 100022...
[Uses get_medications tool]
```

## Requirements

- Python 3.12+
- Docker (for mock server)
- [mise](https://mise.run) (recommended) or [uv](https://github.com/astral-sh/uv)