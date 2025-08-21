# Development Guide

This guide covers everything you need to develop, test, and extend the Vista API MCP Server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Running the Server](#running-the-server)
4. [Client Setup](#client-setup)
5. [Example Usage](#example-usage)
6. [Configuration](#configuration)
7. [Project Structure](#project-structure)
8. [Development Workflow](#development-workflow)
9. [Adding New Tools](#adding-new-tools)
10. [Testing](#testing)
11. [Code Quality](#code-quality)
12. [Architecture Overview](#architecture-overview)
13. [Transport Modes](#transport-modes)
14. [Troubleshooting](#troubleshooting)

## 1. Prerequisites

- Python 3.12 or higher
- [mise](https://mise.jdx.dev/) (formerly rtx) for environment management
- Docker (optional, for Redis)
- Vista API credentials (contact your Vista administrator)

## 2. Initial Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-org/vista-api-mcp-server.git
   cd vista-api-mcp-server
   ```

2. **Install mise and trust the configuration:**

   ```bash
   # Install mise (if not already installed)
   curl https://mise.jdx.dev/install.sh | sh
   
   # Trust the mise configuration
   mise trust
   ```

3. **Install dependencies (automatic with mise):**

   ```bash
   # Dependencies are automatically installed when you run any mise command
   mise run dev  # This will trigger installation if needed
   ```

4. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your Vista API credentials
   ```

## 3. Running the Server

### With Mock Server (Development)

The mock server simulates the Vista API for local development without needing real Vista access:

```bash
# Start both mock server and MCP server
mise run dev-with-mock

# Or run them separately:
mise run mock-server  # In one terminal
mise run dev         # In another terminal
```

### Without Mock Server (Production/Staging)

When connecting to a real Vista API instance:

```bash
# Standard stdio mode
mise run dev

# HTTP mode for remote access
mise run dev-http
```

### Available mise Commands

```bash
mise tasks  # List all available commands

# Key commands:
mise run dev              # Run MCP server in stdio mode
mise run dev-http         # Run MCP server in HTTP mode
mise run dev-with-mock    # Run with mock Vista API
mise run mock-server      # Run mock server only
mise run test            # Run tests
mise run lint            # Run linting and formatting
mise run format          # Format code with black
mise run typecheck       # Run mypy type checking
```

## 4. Client Setup

Once you have the Vista API MCP Server running, you need to configure your LLM client to connect to it. This is how you configure Claude Desktop. You can also use Continue.dev or other clients.

### Claude Desktop

Claude Desktop has native MCP support and works best with the stdio transport mode. 

```bash
# Run the setup script
python scripts/setup_claude_desktop.py

# Verify configuration
python scripts/test_config.py --client=claude
```

Verifying Claude Desktop Connection:
1. Restart Claude Desktop after configuration changes
2. Start a new conversation
3. Look for the Vista API tools in the available tools list
4. Test with a simple query: "What tools are available for Vista?"

## 5. Example Usage

Once configured in your LLM client:

```
You: "Search for patients with last name ANDERSON"
Assistant: I'll search for patients with the last name Anderson...
[Uses search_patients tool]

You: "Show medications for patient 100022"
Assistant: I'll retrieve the medications for patient 100022...
[Uses get_medications tool]
```

## 6. Configuration

This section covers configuration for local development, testing, and client connections. For production deployment configuration, see the [Deployment Guide](add link).

### Environment Variables

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

### Client Configuration Files

Example configuration files are included in the repository:

- `.claude_desktop_config.example.json` - Claude Desktop template
- `.cursorrules.example` - Cursor IDE template

### Redis Configuration

#### Local Development

Redis caching is optional but recommended for better performance:

```bash
# Start Redis with Docker
docker run -d -p 6379:6379 redis:alpine

# Configure in .env
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379
```

#### Testing Redis Connection

```python
# Test script
python -c "
from src.services.cache.factory import CacheFactory
import asyncio

async def test():
    cache = await CacheFactory.create_patient_cache()
    print(f'Cache backend: {type(cache).__name__}')
    
asyncio.run(test())
"
```

## 7. Project Structure

```
vista-api-mcp-server/
├── src/
│   ├── __main__.py              # Entry point
│   ├── config.py                # Configuration management
│   ├── models/                  # Data models
│   │   ├── patient/            # Patient-specific models
│   │   ├── vista/              # Vista API response models
│   │   └── responses/          # Tool response models
│   ├── services/               # Business logic services
│   │   ├── cache/             # Caching implementation
│   │   ├── data/              # Data access layer
│   │   ├── filters/           # Data filtering utilities
│   │   ├── formatters/        # Output formatting
│   │   ├── parsers/           # Response parsing
│   │   ├── rpc/               # RPC execution helpers
│   │   └── validators/        # Input validation
│   ├── tools/                  # MCP tool implementations
│   │   ├── admin/             # Administrative tools
│   │   ├── clinical/          # Clinical data tools
│   │   ├── patient/           # Patient data tools
│   │   └── system/            # System utilities
│   ├── vista/                  # Vista API client
│   │   ├── auth/              # Authentication/JWT handling
│   │   ├── base.py            # Base client interface
│   │   └── client.py          # Vista API client implementation
│   └── utils.py               # Common utilities
├── mock_server/               # Mock Vista API implementation
│   └── src/                   # Mock server source code
├── tests/                     # Test suite
├── mise.toml                  # mise configuration
└── pyproject.toml            # Python project configuration
```

## 8. Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Follow the existing patterns in the codebase. Key principles:

- Use type hints for all functions
- Follow the service-oriented architecture
- Keep tools focused on their specific domain
- Use the existing RPC executor for Vista API calls

### 3. Test Your Changes

```bash
# Run all tests
mise run test

# Run specific test
pytest tests/test_your_feature.py -v

# Run with coverage
pytest --cov=src tests/
```

### 4. Lint and Format

```bash
# Always run lint before committing
mise run lint

# This runs:
# - black (formatter)
# - ruff (linter)
# - mypy (type checker)
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

## 9. Adding New Tools

### 1. Choose the Right Module

Tools are organized by domain:

- `tools/patient/` - Patient data retrieval
- `tools/clinical/` - Clinical data (medications, labs, vitals)
- `tools/admin/` - Administrative functions
- `tools/system/` - System utilities

### 2. Key Patterns to Follow

- Use the RPC executor service for all Vista API calls
- Use parameter builders for RPC parameters
- Use validators for input validation
- Use formatters for output formatting
- Return structured responses using Pydantic models

## 10. Testing

### Running Tests

```bash
# Run all tests
mise run test

# Run with verbose output
mise run test -- -v

# Run specific test file
pytest tests/test_patient_tools.py

# Run with coverage
pytest --cov=src tests/
```

### Test Data

See [TEST_DATA.md](TEST_DATA.md) for:

- Test patient IDs
- Test credentials
- Sample data reference

### Writing Tests

```python
# Example test
async def test_get_patient_demographics():
    """Test patient demographics retrieval"""
    result = await get_patient_demographics(
        patient_dfn="100022",
        station="500"
    )
    
    assert result["success"] is True
    assert result["patient"]["name"] == "CARTER,DAVID"
    assert "***-**-" in result["patient"]["ssn"]
```

## 11. Code Quality

### Linting and Formatting

Always run linting before committing:

```bash
mise run lint
```

This runs:

- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking

### Type Hints

Always use type hints:

```python
from typing import Any, Optional

async def get_patient_data(
    patient_dfn: str,
    station: Optional[str] = None,
) -> dict[str, Any]:
    """Function with proper type hints"""
    pass
```

### Import Organization

Imports are automatically organized by `ruff`. Standard order:

1. Standard library imports
2. Third-party imports
3. Local imports

## 12. Architecture Overview

### Core Components

1. **MCP Server** (`src/__main__.py`)
   - Handles MCP protocol communication
   - Registers and exposes tools
   - Manages sessions and authentication

2. **Vista Client** (`src/vista/client.py`)
   - Async HTTP client for Vista API
   - JWT token management
   - Automatic token refresh

3. **Tools** (`src/tools/`)
   - Individual functions exposed to LLM
   - Domain-specific organization
   - Standardized error handling

4. **Services** (`src/services/`)
   - Business logic layer
   - Caching, parsing, formatting
   - RPC execution helpers

### Data Flow

```
LLM Client → MCP Server → Tool Function → Services → Vista Client → Vista API
                ↑                              ↓
                └──────── Response ────────────┘
```

### Security Model

- JWT-based authentication with Vista API
- Token refresh handled automatically
- Station-based access control
- No PHI logging

## 13. Transport Modes

### stdio Mode (Default)

- Communication via standard input/output
- Best for local development
- Used by Claude Desktop

```bash
mise run dev
```

### HTTP/SSE Mode

- Server-Sent Events over HTTP
- Enables remote connections
- Better for debugging

```bash
mise run dev-sse
# Access at http://localhost:8808/sse
```

## 14. Troubleshooting

### Common Issues

1. **Import errors after changes:**

   ```bash
   # Clear Python cache
   find . -type d -name __pycache__ -exec rm -rf {} +
   ```

2. **Type checking failures:**

   ```bash
   # Run mypy directly for detailed errors
   mypy src/
   ```

3. **Mock server connection issues:**

   ```bash
   # Check if mock server is running
   curl http://localhost:8888/auth/token
   ```

4. **Token expiration errors:**
   - Check `VISTA_TOKEN_REFRESH_BUFFER_SECONDS` in .env
   - Default is 30 seconds before expiry

### Debug Logging

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
MCP_LOG_LEVEL=DEBUG
```

### Getting Help

1. Check the error messages - they're designed to be helpful
2. Review the test files for usage examples
3. Check the mock server implementation for API behavior
4. Open an issue on GitHub for bugs or questions

## Tool Reference

### Patient Tools

#### get_patient_vitals

Retrieve vital sign measurements for a patient.

**Parameters:**

- `patient_dfn` (required): Patient DFN
- `station`: Vista station number (optional)
- `vital_type`: Filter by type (BLOOD PRESSURE, PULSE, etc.)
- `days_back`: History period (1-365, default: 30)

#### get_patient_labs

Get laboratory test results.

**Parameters:**

- `patient_dfn` (required): Patient DFN
- `station`: Vista station number (optional)
- `abnormal_only`: Return only abnormal results (default: false)
- `lab_type`: Filter by test name (optional)
- `days_back`: History period (1-730, default: 90)

#### get_patient_summary

Generate comprehensive clinical summary.

**Parameters:**

- `patient_dfn` (required): Patient DFN
- `station`: Vista station number (optional)

#### get_patient_consults

Retrieve consultation requests.

**Parameters:**

- `patient_dfn` (required): Patient DFN
- `station`: Vista station number (optional)
- `active_only`: Filter active only (default: true)

### System Tools

#### get_current_user

Get current authenticated user context.

**Parameters:** None

#### heartbeat

Check server connectivity.

**Parameters:**

- `station`: Vista station number (optional)

#### get_server_time

Get Vista server time.

**Parameters:**

- `station`: Vista station number (optional)

#### get_intro_message

Get system welcome message.

**Parameters:**

- `station`: Vista station number (optional)

#### get_user_info

Get detailed user information.

**Parameters:**

- `user_duz`: User DUZ (optional)
- `station`: Vista station number (optional)

#### get_server_version

Get Vista version information.

**Parameters:**

- `station`: Vista station number (optional)

### Authentication Tool

#### authenticate_user

Authenticate and get JWT token.

**Parameters:**

- `access_code`: Vista access code
- `verify_code`: Vista verify code
- `station`: Vista station number
