# Setup Guide

Complete setup instructions for the Vista API MCP Server.

## Prerequisites

- Python 3.12 or higher
- Docker Desktop (for mock server)
- [mise](https://mise.run) (recommended) or [uv](https://github.com/astral-sh/uv) package manager

## Quick Setup (Recommended)

### 1. Install mise

```bash
# macOS/Linux
curl https://mise.run | sh

# Windows
winget install mise
```

### 2. Clone and Setup

```bash
git clone <repository>
cd octo-vista-api-x-mcp-server

# Trust the mise configuration
mise trust

# Start with mock server (recommended for development)
mise run dev-with-mock
```

That's it! This command automatically:
- Installs Python 3.12
- Creates virtual environment
- Installs all dependencies
- Generates RSA keys for mock authentication
- Starts the mock Vista API server
- Launches MCP inspector at http://localhost:6274

## Manual Setup (Alternative)

If you prefer manual setup or can't use mise:

### 1. Install Python 3.12+

```bash
# Check Python version
python --version  # Should be 3.12 or higher
```

### 2. Install uv

```bash
pip install uv
```

### 3. Install Dependencies

```bash
cd octo-vista-api-x-mcp-server
uv sync
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Start Mock Server

```bash
cd mock_server
docker-compose up -d
```

### 6. Run MCP Server

```bash
uv run mcp dev server.py:server
```

## Claude Desktop Integration

### Quick Setup (Recommended)

```bash
mise run setup-claude
```

This automated script will configure Claude Desktop for you.

### Manual Setup

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vista-api": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/octo-vista-api-x-mcp-server",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "VISTA_API_BASE_URL": "http://localhost:8080",
        "VISTA_API_KEY": "test-wildcard-key-456",
        "DEFAULT_STATION": "500",
        "DEFAULT_DUZ": "10000000219"
      }
    }
  }
}
```

### 2. Find uv Path

```bash
which uv
# Use this path in the config above
```

### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop to load the new configuration.

## Environment Configuration

### Environment Variables

```env
# Vista API endpoint (can be mock server or real Vista API X)
VISTA_API_BASE_URL=http://localhost:8080
VISTA_API_KEY=test-wildcard-key-456

# Default context
DEFAULT_STATION=500
DEFAULT_DUZ=10000000219

# Debug logging
VISTA_MCP_DEBUG=false
```

For production Vista API X:
```env
VISTA_API_BASE_URL=https://your-vista-api-x-server
VISTA_API_KEY=your-production-api-key
```

## Verify Installation

### 1. Check Mock Server

```bash
curl http://localhost:8080/health
# Should return: {"status": "healthy"}
```

### 2. Test MCP Server

In the MCP inspector (http://localhost:6274):
1. Click "Connect"
2. Try calling the `heartbeat` tool
3. Search for patients with `search_patients`

### 3. Test in Claude Desktop

After restarting Claude Desktop:
- Look for "vista-api" in the MCP servers list
- Ask: "Can you search for patients in Vista?"

## Troubleshooting

### Port Already in Use

```bash
# Stop mock server
mise run stop-mock
# or
docker-compose -f mock_server/docker-compose.yml down
```

### Module Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall
```

### Claude Desktop Not Finding Server

1. Verify absolute paths in config
2. Check uv is accessible: `which uv`
3. Test server manually: `uv run python server.py`
4. Check Claude Desktop logs

### Docker Not Running

Start Docker Desktop application and wait for it to fully start.

## Next Steps

- Read [TOOLS.md](TOOLS.md) to understand available tools
- See [DEVELOPMENT.md](DEVELOPMENT.md) for extending the server
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design details