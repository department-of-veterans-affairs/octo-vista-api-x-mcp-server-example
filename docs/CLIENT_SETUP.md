# LLM Client Setup Guide

This guide explains how to connect the Vista API MCP Server to various LLM clients that support the Model Context Protocol (MCP).

## Table of Contents

- [Claude Desktop](#claude-desktop)
- [Cursor](#cursor)
- [Zed](#zed)
- [VS Code (Cline Extension)](#vs-code-cline-extension)
- [Custom MCP Clients](#custom-mcp-clients)

## Claude Desktop

Claude Desktop has built-in MCP support. Follow these steps to connect:

### 1. Prerequisites

- Claude Desktop installed
- Vista API MCP Server set up (`mise run dev-with-mock`)
- Mock server running (if using mock)

### 2. Automatic Setup (Recommended)

Run the setup script for automatic configuration:

```bash
python scripts/setup_claude_desktop.py
```

This script will:

- Find your uv installation
- Locate your Claude Desktop config
- Add the Vista API server
- Optionally start the mock server

### 3. Manual Configuration

Edit the Claude configuration file:

**macOS/Linux:**

```bash
~/.config/Claude/claude_desktop_config.json
```

**Windows:**

```
%APPDATA%\Claude\claude_desktop_config.json
```

Add the Vista API server configuration:

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
        "VISTA_API_BASE_URL": "http://localhost:8888",
        "VISTA_API_KEY": "test-wildcard-key-456",
        "DEFAULT_STATION": "500",
        "DEFAULT_DUZ": "10000000219"
      }
    }
  }
}
```

### 4. Find Your Paths

**Find uv path:**

```bash
which uv
# Example output: /Users/username/.local/bin/uv
```

**Find project path:**

```bash
cd octo-vista-api-x-mcp-server
pwd
# Example output: /Users/username/projects/octo-vista-api-x-mcp-server
```

### 5. Complete Examples

#### stdio Transport (Local)

```json
{
  "mcpServers": {
    "vista-api": {
      "command": "/Users/john/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/john/projects/octo-vista-api-x-mcp-server",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "VISTA_API_BASE_URL": "http://localhost:8888",
        "VISTA_API_KEY": "test-wildcard-key-456",
        "DEFAULT_STATION": "500",
        "DEFAULT_DUZ": "10000000219"
      }
    }
  }
}
```

#### SSE Transport (Remote Access)

For local development:

```json
{
  "mcpServers": {
    "vista-api": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

For production (with your deployed server):

```json
{
  "mcpServers": {
    "vista-api": {
      "url": "https://your-mcp-server.com/sse"
    }
  }
}
```

### 6. Restart Claude Desktop

1. Completely quit Claude Desktop (not just close the window)
2. Start Claude Desktop again
3. Look for "vista-api" in the MCP servers list (🔌 icon)

### 7. Test the Connection

Try these prompts in Claude:

- "Search for patients with last name ANDERSON"
- "Show medications for patient 100022"
- "Get vital signs for patient 100023"

## Cursor

Cursor IDE has MCP support through configuration. Here's how to set it up:

### 1. Prerequisites

- Cursor IDE installed
- Vista API MCP Server set up
- Python environment configured

### 2. Configuration

Create or edit `.cursorrules` in your project root:

```json
{
  "mcpServers": {
    "vista-api": {
      "command": "uv",
      "args": [
        "--directory",
        ".",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "VISTA_API_BASE_URL": "http://localhost:8888",
        "VISTA_API_KEY": "test-wildcard-key-456",
        "DEFAULT_STATION": "500",
        "DEFAULT_DUZ": "10000000219"
      },
      "cwd": "/path/to/octo-vista-api-x-mcp-server"
    }
  }
}
```

### 3. Alternative: Cursor Settings

You can also configure MCP servers in Cursor's settings:

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP"
3. Add server configuration in the MCP Servers section

### 4. Using in Cursor

Once configured, you can use the Vista API tools in:

- Chat panel
- Inline code generation
- Command palette (search for "MCP")

Example usage in Cursor chat:

```
@vista-api search for patient THOMPSON
@vista-api get medications for patient 100024
```

## Zed

Zed editor supports MCP through its assistant feature:

### 1. Configuration

Edit `~/.config/zed/settings.json`:

```json
{
  "assistant": {
    "mcp_servers": {
      "vista-api": {
        "command": "/path/to/uv",
        "args": [
          "--directory",
          "/path/to/octo-vista-api-x-mcp-server",
          "run",
          "python",
          "server.py"
        ],
        "env": {
          "VISTA_API_BASE_URL": "http://localhost:8888",
          "VISTA_API_KEY": "test-wildcard-key-456"
        }
      }
    }
  }
}
```

### 2. Usage

- Open Zed Assistant (Cmd/Ctrl + ?)
- The Vista API tools will be available
- Use natural language to interact with patient data

## VS Code (Cline Extension)

The Cline extension adds MCP support to VS Code:

### 1. Install Cline

```bash
code --install-extension saoudrizwan.claude-dev
```

### 2. Configuration

Add to VS Code settings.json:

```json
{
  "cline.mcpServers": {
    "vista-api": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/octo-vista-api-x-mcp-server",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "VISTA_API_BASE_URL": "http://localhost:8888",
        "VISTA_API_KEY": "test-wildcard-key-456",
        "DEFAULT_STATION": "500",
        "DEFAULT_DUZ": "10000000219"
      }
    }
  }
}
```

### 3. Usage

1. Open Cline panel (View > Cline)
2. Vista API tools will be available
3. Use @ mentions to access tools

## Custom MCP Clients

You can connect any MCP-compatible client using the standard protocol:

### Python Example

```python
import asyncio
from mcp import ClientSession, StdioServerParameters

async def main():
    # Configure server connection
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "--directory",
            "/path/to/octo-vista-api-x-mcp-server",
            "run",
            "python",
            "server.py"
        ],
        env={
            "VISTA_API_BASE_URL": "http://localhost:8888",
            "VISTA_API_KEY": "test-wildcard-key-456"
        }
    )
    
    # Connect and use
    async with ClientSession(server_params) as session:
        # Initialize connection
        await session.initialize()
        
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Search for patients
        result = await session.call_tool(
            "search_patients",
            arguments={"search_term": "ANDERSON"}
        )
        print(f"Search results: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Node.js Example

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "uv",
    args: [
      "--directory",
      "/path/to/octo-vista-api-x-mcp-server",
      "run",
      "python",
      "server.py"
    ],
    env: {
      VISTA_API_BASE_URL: "http://localhost:8888",
      VISTA_API_KEY: "test-wildcard-key-456"
    }
  });

  const client = new Client({
    name: "vista-client",
    version: "1.0.0"
  }, {
    capabilities: {}
  });

  await client.connect(transport);

  // List available tools
  const tools = await client.listTools();
  console.log("Available tools:", tools);

  // Search for patients
  const result = await client.callTool({
    name: "search_patients",
    arguments: { search_term: "ANDERSON" }
  });
  console.log("Search results:", result);

  await client.close();
}

main().catch(console.error);
```

## Troubleshooting

### Common Issues

**1. Server not starting**

- Check if mock server is running: `curl http://localhost:8888/health`
- Verify uv path is correct: `which uv`
- Check Python version: `python --version` (needs 3.12+)

**2. Authentication errors**

- Ensure `VISTA_API_KEY` is set correctly
- Verify mock server has test data loaded
- Check if using correct station number (500)

**3. Client can't find server**

- Use absolute paths in configuration
- Restart the client application completely
- Check client logs for error messages

**4. Permission denied**

- Make sure server.py is executable: `chmod +x server.py`
- Check directory permissions

### Debug Mode

Enable debug logging by setting in the environment:

```json
"env": {
  "VISTA_MCP_DEBUG": "true",
  // ... other settings
}
```

### Testing Connection

Test the server directly:

```bash
# Start server manually
cd /path/to/octo-vista-api-x-mcp-server
VISTA_API_BASE_URL=http://localhost:8888 \
VISTA_API_KEY=test-wildcard-key-456 \
uv run python server.py
```

You should see initialization messages if it's working correctly.

## Best Practices

1. **Use environment variables** for sensitive data:

   ```json
   "env": {
     "VISTA_API_BASE_URL": "${VISTA_API_BASE_URL}",
     "VISTA_API_KEY": "${VISTA_API_KEY}"
   }
   ```

2. **Start mock server first** when developing:

   ```bash
   mise run dev-with-mock
   ```

3. **Test with simple queries** before complex workflows:
   - Start with `heartbeat` tool
   - Then try `search_patients`
   - Progress to multi-tool workflows

4. **Monitor logs** for troubleshooting:
   - MCP server logs show tool calls
   - Mock server logs show API requests
   - Client logs show connection issues

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Vista API MCP Tools Reference](TOOLS.md)
- [Example Prompts](PROMPTS.md)
- [Testing Guide](TESTING.md)
