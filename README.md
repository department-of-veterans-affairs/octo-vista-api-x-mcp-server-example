# Vista API MCP Server

MCP (Model Context Protocol) server that provides natural language access to VistA healthcare data through Vista API X.

## Quick Start

### Option 1: stdio Transport (Local Development)

```bash
# Traditional stdio mode with MCP inspector
mise run dev-with-mock
```

### Option 2: HTTP Transport (Remote Access) - RECOMMENDED

```bash
# Modern Streamable HTTP server mode accessible via URL
mise run dev-http-with-mock
```

Then connect via URL: `http://localhost:8000/mcp`

### Option 3: VS Code Dev Container (Windows/Podman)

For Windows users with restricted environments:

```bash
# See docs/DEVCONTAINER.md for setup instructions
```

## Features

- **VistA Tools**: Patient search and data retrieval, system utilities
- **Mock Server Included**: Full Vista API X mock for development
- **Multiple Transports**: stdio for local dev, Streamable HTTP for remote access
- **Modern Architecture**: Uses latest MCP Streamable HTTP transport for better performance
- **LLM Client Ready**: Works with any MCP-compatible client
- **Type-Safe**: Full type hints and validation
- **Production Ready**: Docker support for easy deployment

## Client Setup

Connect the Vista API MCP Server to your favorite LLM:

- **[Claude Desktop](docs/DEVELOPMENT.md#claude-desktop)** - Native MCP support
- **[Continue.dev](docs/DEVELOPMENT.md#vs-code-with-continuedev)** - AI-powered development assistant
- **[Other Clients](docs/DEVELOPMENT.md#other-clients)** - HTTP mode for any client

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

# Run the HTTP server
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

- [Development Guide](docs/DEVELOPMENT.md) - Complete guide for developers including:
  - Setup and installation
  - Running with/without mock server
  - Client configuration (Claude, Continue.dev, etc.)
  - Adding new tools
  - Architecture overview
  - Tool reference
- [Test Data](docs/TEST_DATA.md) - Test patient IDs and credentials
- [Deployment](docs/DEPLOYMENT.md) - Production deployment guide

## Example Usage

Once configured in your LLM client:

```
You: "Show medications for patient 100022"
Assistant: I'll retrieve the medications for patient 100022...
[Uses get_medications tool]

You: "Get vital signs for patient 100022"
Assistant: I'll retrieve the vital signs for patient 100022...
[Uses get_patient_vitals tool]
```

**Note:** Patient context (DFN) should be injected by CPRS, not searched from MCP tools.

## Requirements

- Python 3.12+
- Docker (for mock server)
- [mise](https://mise.run) (recommended) or [uv](https://github.com/astral-sh/uv)
