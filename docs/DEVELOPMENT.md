# Development Guide

Guide for developing and extending the Vista API MCP Server.

## Development Setup

### Prerequisites

- Python 3.12+
- Docker Desktop
- Git
- IDE with Python support (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository>
cd octo-vista-api-x-mcp-server

# Setup with mise (recommended)
mise trust
mise run dev-with-mock

# Or manual setup
uv sync
```

## Project Structure

```
octo-vista-api-x-mcp-server/
├── src/                    # Source code
│   ├── api_clients/        # API client implementation
│   │   ├── base.py         # Abstract base client
│   │   └── vista_client.py # Vista API X client
│   ├── tools/              # MCP tool implementations
│   │   ├── patient.py      # Patient-related tools
│   │   ├── clinical.py     # Clinical data tools
│   │   ├── admin.py        # Administrative tools
│   │   └── system.py       # System tools
│   ├── models.py           # Pydantic models
│   ├── parsers.py          # Vista data parsers
│   ├── prompts.py          # MCP prompts
│   ├── resources.py        # MCP resources
│   └── utils.py            # Utility functions
├── mock_server/            # Mock Vista API X server
├── scripts/                # Helper scripts
├── tests/                  # Test files
├── docs/                   # Documentation
└── server.py               # Main entry point
```

## Adding New Tools

### 1. Define the Tool Function

Create a new tool in the appropriate module (e.g., `src/tools/clinical.py`):

```python
from mcp.server.fastmcp import FastMCP
from ..models import StandardResponse
from ..api_clients.base import BaseVistaClient

@mcp.tool(
    name="get_new_data",
    description="Get new clinical data type"
)
async def get_new_data(
    patient_id: str,
    client: BaseVistaClient
) -> StandardResponse:
    """
    Get new data for a patient.
    
    Args:
        patient_id: Patient ID (DFN/IEN)
        client: Vista API client instance
    
    Returns:
        Structured response with data
    """
    try:
        # Call Vista RPC
        result = await client.invoke_rpc(
            rpc_name="NEW DATA RPC",
            params={"patientId": patient_id}
        )
        
        # Parse and structure response
        data = parse_new_data(result)
        
        return StandardResponse(
            success=True,
            data=data,
            message=f"Retrieved {len(data)} items"
        )
    except Exception as e:
        return StandardResponse(
            success=False,
            error=str(e),
            message="Failed to retrieve data"
        )
```

### 2. Add Parser if Needed

Add parsing logic in `src/parsers.py`:

```python
def parse_new_data(raw_data: str) -> List[Dict[str, Any]]:
    """Parse Vista delimited format into structured data"""
    lines = raw_data.strip().split('\n')
    results = []
    
    for line in lines:
        if line:
            parts = line.split('^')
            results.append({
                "id": parts[0],
                "value": parts[1],
                # ... map other fields
            })
    
    return results
```

### 3. Register the Tool

The tool is automatically registered via the `@mcp.tool` decorator, but ensure the module is imported in `server.py`.

## Testing

### Run Tests

```bash
# Run all tests
mise run test

# Run specific test
uv run pytest tests/test_clinical_tools.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Write Tests

Create test files in `tests/`:

```python
import pytest
from src.tools.clinical import get_new_data
from src.api_clients.vista_client import VistaAPIClient

@pytest.mark.asyncio
async def test_get_new_data():
    # Use test/mock endpoint
    client = VistaAPIClient(
        base_url="http://localhost:8080",
        api_key="test-wildcard-key-456"
    )
    result = await get_new_data(
        patient_id="100022",
        client=client
    )
    
    assert result.success
    assert len(result.data) > 0
    assert result.data[0]["id"] is not None
```

### Test in MCP Inspector

1. Start development server: `mise run dev-with-mock`
2. Open http://localhost:6274
3. Test your new tool with various parameters

## Code Quality

### Formatting and Linting

#### Automatic Formatting (VS Code/Cursor)

The project includes VS Code/Cursor settings for automatic formatting on save:
- **Black**: Python code formatting
- **Ruff**: Linting with auto-fix
- **Import sorting**: Automatic organization of imports
- **EditorConfig**: Consistent file formatting across editors

To enable auto-formatting:
1. Open the project in VS Code or Cursor
2. Install recommended extensions when prompted
3. Files will automatically format when saved

#### Manual Formatting

```bash
# Format code
mise run lint

# Or manually
uv run black src/
uv run ruff check src/ --fix
```

### Type Checking

```bash
uv run mypy src/
```

### Pre-commit Checks

```python
# In your code
from typing import List, Dict, Any, Optional

# Use type hints everywhere
async def process_data(
    patient_id: str,
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    ...
```

## Debugging

### Enable Debug Logging

```bash
# Set in .env or environment
VISTA_MCP_DEBUG=true

# Or when running
VISTA_MCP_DEBUG=true mise run dev-with-mock
```

### Debug in VS Code

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug MCP Server",
            "type": "python",
            "request": "launch",
            "program": "server.py",
            "console": "integratedTerminal",
            "env": {
                "API_CLIENT_TYPE": "mock",
                "VISTA_MCP_DEBUG": "true"
            }
        }
    ]
}
```

### Common Issues

1. **Import Errors**: Ensure you're running from project root
2. **Mock Data**: Add test data in `mock_server/src/data/`
3. **RPC Errors**: Check RPC name and parameters match Vista specs

## Working with Mock Server

### Adding Mock Data

Edit files in `mock_server/src/data/`:
- `test_patients.py` - Patient demographics
- `clinical_data.py` - Clinical information
- `appointments.py` - Scheduling data

### Adding New RPCs

1. Add handler in `mock_server/src/rpc/handlers/`
2. Register in RPC registry
3. Add test data as needed

## Contributing

### Code Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to all functions
- Keep functions focused and small
- Handle errors gracefully

### Pull Request Process

1. Create feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit PR with clear description

### Documentation

- Update TOOLS.md when adding tools
- Add usage examples
- Document any new environment variables
- Keep README files current

## Performance Considerations

### Caching

Use the built-in cache for expensive operations:

```python
from cachetools import TTLCache
from ..utils import get_cache

cache = get_cache()

@cache.cached(key=lambda patient_id: f"labs_{patient_id}")
async def get_cached_labs(patient_id: str):
    # Expensive operation
    return await fetch_labs(patient_id)
```

### Async Best Practices

- Use `asyncio.gather()` for parallel operations
- Don't block the event loop
- Handle timeouts appropriately

### Data Limits

- Implement pagination for large datasets
- Use date ranges to limit data
- Consider response size for Claude