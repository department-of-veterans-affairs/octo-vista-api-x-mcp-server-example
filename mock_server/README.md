# Vista API X Mock Server

Mock implementation of Vista API X for local development and testing.

## Quick Start

```bash
# Generate RSA keys for JWT signing (first time only)
cd scripts
python generate_rsa_keys.py
cd ..

# Start the mock server
docker-compose up -d

# Check it's running
curl http://localhost:8080/health
```

## Endpoints

- **API**: http://localhost:8080
- **Health Check**: http://localhost:8080/health
- **API Docs**: http://localhost:8080/docs

## Authentication

Get a token:
```bash
curl -X POST http://localhost:8080/auth/token \
  -H "Content-Type: application/json" \
  -d '{"key": "test-wildcard-key-456"}'
```

Use the token:
```bash
curl -X POST http://localhost:8080/vista-sites/500/users/10000000219/rpc/invoke \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "OR CPRS GUI CHART",
    "rpc": "ORWU DT",
    "parameters": []
  }'
```

## Test Data

**API Keys:**
- `test-standard-key-123` - Standard access
- `test-wildcard-key-456` - Full access (recommended)
- `test-limited-key-789` - Limited access

**Test Patients:** DFN 100022-100029 (8 patients)

**Test Station:** 500 (Washington DC VAMC)

**Test User:** DUZ 10000000219

## Development

```bash
# Install dependencies
uv sync

# Generate RSA keys (if not already present)
cd scripts
python generate_rsa_keys.py
cd ..

# Run locally (without Docker)
uv run uvicorn src.main:app --reload

# Run tests
uv run pytest
```

## Documentation

See [docs/API.md](docs/API.md) for detailed API reference and examples.