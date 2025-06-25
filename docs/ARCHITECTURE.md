# Architecture

System architecture and design decisions for the Vista API MCP Server.

## Overview

The Vista API MCP Server provides a bridge between LLM clients (via MCP) and VistA systems through the Vista API X interface. It follows a modular, extensible architecture with swappable backend implementations.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   LLM Client    │────▶│   MCP Server     │────▶│  Vista API X    │
│  (e.g. Claude)  │ MCP │                  │HTTP │  (Real/Mock)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                        ┌──────┴──────┐
                        │   Tools     │
                        │  Registry   │
                        └─────────────┘
```

## System Context

### External Systems

1. **LLM Clients**: Any MCP-compatible client (Claude Desktop, custom implementations)
2. **Vista API X**: RESTful interface to VistA systems
3. **VistA**: Veterans Health Information Systems and Technology Architecture
4. **Mock Server**: Development/testing implementation of Vista API X

### Key Interfaces

- **MCP Protocol**: Standard JSON-RPC communication with LLM clients
- **Vista API X REST**: HTTP/JSON interface to VistA
- **Vista RPC**: Remote Procedure Call protocol within VistA

## Core Components

### MCP Server Layer

Built on FastMCP, providing:

- Tool registration and discovery
- Request/response handling  
- Session management
- Error handling
- Streaming support for large responses

### Vista API Client

The system uses a single `VistaAPIClient` that connects to the Vista API endpoint specified by `VISTA_API_BASE_URL`. This endpoint can be either a mock server for development or a real Vista API X instance for production.

**Key Methods**:

- `invoke_rpc()`: Execute Vista RPC with automatic auth
- `get_patient_data()`: Retrieve VPR data
- `search_patients()`: Patient lookup operations

### Tool Modules

Organized by functional domain:

#### Patient Tools (src/tools/patient.py)

- `search_patients`: Multi-criteria patient search
- `get_patient_demographics`: Full demographic data
- `select_patient`: Context management
- `get_patient_data`: VPR data retrieval
- `get_patient_clinical_summary`: Consolidated view

#### Clinical Tools (src/tools/clinical.py)

- `get_medications`: Active/inactive meds with sig
- `get_lab_results`: Lab data with trends
- `get_vital_signs`: Vital measurements
- `get_problems`: Problem list management
- `get_allergies`: Allergy/ADR data
- `get_notes`: Clinical documentation
- `get_orders`: Order status and details

#### Administrative Tools (src/tools/admin.py)

- `get_appointments`: Scheduling data
- `get_user_profile`: User demographics
- `list_team_members`: Care team info
- `get_clinic_list`: Facility data

#### System Tools (src/tools/system.py)

- `heartbeat`: Keep-alive and monitoring
- `get_server_time`: Time synchronization
- `get_intro_message`: System messages
- `get_user_info`: Context verification
- `get_server_version`: Version tracking

### Data Models (src/models.py)

Pydantic models ensure type safety:

```python
# Core response model
class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any]
    error: Optional[str]
    message: Optional[str]

# Domain models
class Patient(BaseModel):
    id: str
    name: str
    ssn: str
    dob: str
    gender: str
    
class Medication(BaseModel):
    name: str
    dosage: str
    schedule: str
    status: str
    prescriber: str
```

### Parsers (src/parsers.py)

Transform Vista's delimited formats to structured data:

- FileMan date conversion
- Caret-delimited string parsing
- Multi-line report processing
- Error response handling

## Data Flow

### Request Lifecycle

```
1. LLM generates tool call request
2. MCP Server validates request schema
3. Tool function validates business logic
4. API Client adds authentication
5. Vista API X processes RPC
6. Parser transforms response
7. Tool returns structured data
8. MCP Server sends response to LLM
```

### Authentication Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client  │────▶│ Auth Manager │────▶│ Vista API X  │
│          │     │              │     │              │
│          │◀────│ JWT Token    │◀────│ Auth Token   │
└──────────┘     └──────────────┘     └──────────────┘
```

**Token Lifecycle**:

1. Initial authentication with API key
2. JWT token generation (30-60 min TTL)
3. Automatic refresh before expiration
4. Secure in-memory storage only

## Security Architecture

### Defense in Depth

1. **Network Layer**
   - TLS 1.2+ for all external calls
   - Certificate validation
   - Network segmentation

2. **Authentication Layer**
   - RSA-signed JWT tokens
   - API key rotation support
   - Token expiration and refresh

3. **Authorization Layer**
   - Station-based access control
   - User context (DUZ) validation
   - RPC-level permissions
   - Resource-based access

4. **Application Layer**
   - Input validation (Pydantic)
   - Output sanitization
   - Error message filtering
   - Rate limiting ready

### Data Protection

- **No PHI in logs**: Structured logging with PHI exclusion
- **Memory-only secrets**: No credential persistence
- **Audit trail**: All operations logged with context
- **Data minimization**: Only requested data returned

## Mock Server Architecture

Provides high-fidelity VistA simulation:

```
Mock Server Stack
├── FastAPI Application
│   ├── Authentication endpoints
│   ├── RPC invocation handlers
│   └── Error simulation
├── LocalStack
│   └── DynamoDB (auth storage)
├── Test Data Repository
│   ├── 8 patient personas
│   ├── Clinical data sets
│   └── Provider/facility data
└── Docker Compose orchestration
```

**Key Features**:

- Identical API surface to production
- Comprehensive test scenarios
- Configurable error injection
- Performance characteristics simulation

## Performance Architecture

### Caching Strategy

```python
# Three-tier caching
1. JWT Token Cache (30 min TTL)
2. Patient Context Cache (session)
3. Reference Data Cache (24 hour TTL)
```

### Async Operations

- All I/O operations are async
- Concurrent tool execution support
- Non-blocking Vista API calls
- Streaming for large datasets

### Connection Management

- HTTP/2 connection pooling
- Automatic retry with exponential backoff
- Circuit breaker pattern for failures
- Configurable timeouts per operation

### Resource Limits

- Request size limits (10MB)
- Response streaming for large data
- Pagination support for lists
- Rate limiting preparation

## Error Handling

### Error Taxonomy

```
MCP Protocol Errors
├── Transport errors (-32700)
├── Invalid request (-32600)
├── Method not found (-32601)
└── Invalid params (-32602)

Application Errors
├── ValidationError (400)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
└── VistaError (500)
    ├── ConnectionError
    ├── RPCError
    ├── DataError
    └── TimeoutError
```

### Error Response Format

```json
{
  "success": false,
  "error": "AUTHENTICATION_FAILED",
  "message": "Invalid or expired token",
  "details": {
    "vista_error": "SEC-001",
    "rpc": "XUS SIGNON SETUP",
    "station": "500"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Monitoring and Observability

### Metrics

- Request rate and latency
- Error rates by type
- Cache hit ratios
- Vista API response times

### Logging

- Structured JSON logging
- Correlation ID tracking
- PHI-safe log entries
- Configurable log levels

### Health Checks

- `/health` endpoint
- Vista connectivity check
- Authentication validation
- Resource availability

## Deployment Architecture

### Development Environment

```
├── MCP Inspector (localhost:6274)
├── Mock Server (localhost:8080)
├── LocalStack (localhost:4566)
└── Application (stdio/pipes)
```

### Production Environment

```
├── LLM Client (MCP connection)
├── MCP Server (managed process)
├── Vista API X (HTTPS endpoint)
└── Monitoring (logs/metrics)
```

### Configuration Management

**Environment Variables**:

```env
# Core settings
VISTA_API_BASE_URL=http://localhost:8080    # or https://vista-api-x.va.gov
VISTA_API_KEY=${VISTA_API_KEY}
LOG_LEVEL=INFO|DEBUG|ERROR

# Defaults
DEFAULT_STATION=500
DEFAULT_DUZ=10000000219

# Performance tuning
CACHE_TTL=300
MAX_RETRIES=3
TIMEOUT_SECONDS=30
CONNECTION_POOL_SIZE=10
```

## Technology Decisions

### Language: Python 3.12+

- Strong async/await support
- Type hints and validation
- Rich ecosystem for healthcare
- VA standard for many projects

### Framework: FastMCP

- Purpose-built for MCP servers
- Async-first design
- Built-in tool management
- Standard error handling

### Data Validation: Pydantic

- Runtime type checking
- Automatic serialization
- Schema generation
- Performance optimized

### HTTP Client: httpx

- Full async support
- HTTP/2 capable
- Connection pooling
- Timeout management

### Mock Server: FastAPI

- High performance
- Auto-documentation
- WebSocket support
- Production ready

## Future Considerations

### Scalability

- Horizontal scaling via process pools
- Redis for distributed caching
- Message queue for async operations
- Database for audit logs

### Enhanced Features

- Bulk operations support
- Subscription/notification system
- Advanced search capabilities
- Analytics integration

### Integration Options

- Direct VistA FileMan access
- HL7 FHIR transformation
- Other VA APIs (Lighthouse)
- External HIE connectivity
