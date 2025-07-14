# Transport Modes

The Vista API MCP Server supports two transport modes for maximum flexibility:

## stdio Transport (Default)

Traditional process-based communication, ideal for local development.

### When to Use

- Local development and testing
- Direct integration with desktop applications
- Simple setup without network configuration
- Debugging with direct process access

### Configuration

```json
{
  "mcpServers": {
    "vista-api": {
      "command": "uv",
      "args": ["--directory", "/path/to/project", "run", "python", "server.py"],
      "env": {
        "VISTA_API_BASE_URL": "http://localhost:8888"
      }
    }
  }
}
```

### Running

```bash
# Development with MCP inspector
mise run dev-with-mock

# Or directly
uv run python server.py
```

## SSE Transport

Server-Sent Events transport for remote access and web integrations.

### When to Use

- Remote server hosting
- Multiple concurrent clients
- Cloud deployment (AWS, GCP, Azure)
- Web-based integrations
- Container deployments

### Configuration

```json
{
  "mcpServers": {
    "vista-api": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### Running Locally

```bash
# Development with SSE transport
mise run dev-sse-with-mock

# Or directly
VISTA_MCP_TRANSPORT=sse uv run python http_server.py
```

### Production Deployment

#### Docker

```bash
# Build and run
docker build -t vista-mcp-http .
docker run -p 8000:8000 \
  -e VISTA_API_BASE_URL=https://your-vista-api.com \
  -e VISTA_API_KEY=your-key \
  vista-mcp-http
```

#### Docker Compose

**Prerequisites:**

```bash
# Create the shared network (one-time setup)
docker network create vista-network
```

**Build and Run:**

```bash
# Build the image
docker-compose build

# Run in detached mode
docker-compose up -d

# Check status
docker-compose ps
```

**Testing the SSE Server:**

```bash
# Test SSE endpoint
curl -N http://localhost:8000/sse -H "Accept: text/event-stream"
# Expected: event: endpoint
#           data: /messages/?session_id=...

# Test with timeout (for scripts)
curl -m 2 http://localhost:8000/sse -H "Accept: text/event-stream"

# View logs
docker-compose logs -f

# Test with mock Vista API running
cd mock_server && docker-compose up -d && cd ..
docker-compose restart
```

**Cleanup:**

```bash
docker-compose down
# Remove network if needed
docker network rm vista-network
```

#### Cloud Run (Google Cloud)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/vista-mcp
gcloud run deploy vista-mcp \
  --image gcr.io/PROJECT-ID/vista-mcp \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars VISTA_API_BASE_URL=https://your-api.com
```

## Comparison

| Feature | stdio | HTTP/SSE |
|---------|-------|----------|
| Setup Complexity | Simple | Moderate |
| Network Required | No | Yes |
| Multiple Clients | No | Yes |
| Remote Access | No | Yes |
| Debugging | Easy | Moderate |
| Production Ready | No | Yes |
| Performance | Best | Good |

## Environment Variables

Both transports use the same environment variables:

```env
# Vista API Configuration
VISTA_API_BASE_URL=http://localhost:8888
VISTA_API_KEY=your-api-key

# Default Context
DEFAULT_STATION=500
DEFAULT_DUZ=10000000219

# Debug Mode
VISTA_MCP_DEBUG=false

# HTTP-specific (optional)
VISTA_MCP_HTTP_PORT=8000
VISTA_MCP_HTTP_HOST=0.0.0.0
```

## Testing Different Transports

### Test stdio Mode

```bash
# In one terminal
mise run dev-with-mock

# MCP inspector opens automatically
```

### Test SSE Mode

```bash
# In one terminal
mise run dev-sse-with-mock

# In another terminal
curl http://localhost:8000/health

# Configure client to use URL
# http://localhost:8000/mcp
```

## Security Considerations

### stdio Transport

- Runs with user permissions
- No network exposure
- Suitable for trusted local environments

### HTTP/SSE Transport

- Configure CORS appropriately
- Use HTTPS in production
- Implement authentication if needed
- Consider API rate limiting
- Use environment variables for secrets

## Troubleshooting

### stdio Issues

- Check Python path and version
- Verify uv installation
- Ensure proper file permissions

### SSE Issues

- Check port availability (8000)
- Verify network connectivity
- Monitor server logs
- Test SSE endpoint with curl first

### Docker SSE Issues

- **Network not found**: Run `docker network create vista-network`
- **Port already in use**: Check `docker ps` and `lsof -i :8000`
- **Cannot connect to mock**: Ensure mock_server is on same network
- **SSE timeout**: Normal - SSE connections stay open
- **Build fails**: Check Docker daemon is running
- **Health check fails**: SSE endpoint may take time to start

## Best Practices

1. **Development**: Use stdio for fast iteration
2. **Testing**: Use HTTP locally to test remote behavior
3. **Staging**: Deploy HTTP with test Vista API
4. **Production**: Deploy HTTP with proper security

## Migration Guide

To migrate from stdio to HTTP:

1. No code changes needed - same tools work
2. Update client configuration to use URL
3. Deploy HTTP server
4. Test thoroughly
5. Update documentation for users
