# Vista API MCP Server

MCP (Model Context Protocol) server that provides natural language access to VistA healthcare data through Vista API X.

## Quick Start

```bash
# One command to start everything
mise run dev-with-mock
```

This automatically installs dependencies, starts the mock server, and launches the MCP inspector.

## Features

- **20+ VistA Tools**: Patient search, clinical data, administrative functions
- **Mock Server Included**: Full Vista API X mock for development
- **LLM Client Ready**: Works with any MCP-compatible client
- **Type-Safe**: Full type hints and validation

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

## Documentation

- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Client Setup](docs/CLIENT_SETUP.md) - Connect to Claude, Cursor, and other clients
- [Tools Reference](docs/TOOLS.md) - All available MCP tools
- [Example Prompts](docs/PROMPTS.md) - Sample queries and workflows
- [Testing Guide](docs/TESTING.md) - Test data and testing strategies
- [Development](docs/DEVELOPMENT.md) - Contributing and extending
- [Architecture](docs/ARCHITECTURE.md) - System design

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