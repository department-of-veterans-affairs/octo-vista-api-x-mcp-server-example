# Test Structure

This test suite is organized into the following categories:

## Directory Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual components
│   ├── test_datetime_parser.py
│   └── test_value_parser.py
├── services/             # Service layer tests
│   ├── test_jwt_utils.py
│   └── test_vista_client_token_refresh.py
├── tools/                # MCP tool tests (to be implemented)
└── integration/          # Integration tests
    └── test_integration.py
```

## Running Tests

### Run all tests
```bash
mise run test
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit/

# Service tests only
pytest tests/services/

# Tool tests only
pytest tests/tools/

# Integration tests only
pytest tests/integration/
```

### Run with coverage
```bash
pytest --cov=src tests/
```

## Test Categories

### Unit Tests (`unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Examples**: Model validation, data parsing, utility functions
- **No external dependencies**: Uses mocks for all external services

### Service Tests (`services/`)
- **Purpose**: Test service layer components like clients and managers
- **Examples**: JWT handling, Vista client behavior, caching
- **May mock network calls**: But tests actual service logic

### Tool Tests (`tools/`)
- **Purpose**: Test MCP tool implementations
- **Examples**: Patient search, data retrieval, system operations
- **Uses mock Vista client**: Tests tool logic without real API calls

### Integration Tests (`integration/`)
- **Purpose**: Test component interactions
- **Examples**: Cache integration, data flow between components
- **May use real services**: But typically with test data

## Writing New Tests

1. **Choose the right category** based on what you're testing
2. **Use fixtures from conftest.py** for common test data
3. **Follow existing patterns** in each test category
4. **Mock external dependencies** appropriately
5. **Test both success and error cases**

## Test Data

Common test data is provided via fixtures in `conftest.py`:
- `mock_vista_client`: Mock Vista API client
- `mcp_server`: Test MCP server instance
- `sample_patient_data`: Sample patient data structure
- `sample_rpc_response`: Sample RPC response format