# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Vista API MCP Server.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Authentication Problems](#authentication-problems)
4. [Connection Issues](#connection-issues)
5. [Performance Problems](#performance-problems)
6. [Debug Mode](#debug-mode)
7. [Log Analysis](#log-analysis)
8. [Error Codes Reference](#error-codes-reference)
9. [Advanced Troubleshooting](#advanced-troubleshooting)
10. [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Commands

```bash
# Check if MCP server is running
python run.py dev --help

# Test mock server connectivity
curl http://localhost:8888/health

# Test production Vista API connectivity
curl -X POST https://your-vista-api.va.gov/auth/token \
  -H "Content-Type: application/json" \
  -d '{"key": "your-api-key"}'

# Check Redis cache (if enabled)
docker exec vista-redis redis-cli PING

# View current configuration
python -c "from src.config import get_vista_config, get_cache_config; print('Vista:', get_vista_config()); print('Cache:', get_cache_config())"
```

### Environment Verification

```bash
# Check if all required environment variables are set
python scripts/check_config.py

# Verify Python dependencies
pip check

# Check Docker containers (if using mock server)
docker ps | grep vista
```

## Common Issues

### 1. Import Errors After Changes

**Symptoms:**
- `ModuleNotFoundError` or `ImportError` after code changes
- Tools not loading properly

**Solution:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# Restart the server
python run.py dev
```

### 2. Type Checking Failures

**Symptoms:**
- `mypy` errors during linting
- Type annotation issues

**Solution:**
```bash
# Run mypy directly for detailed errors
mypy src/

# Check specific file
mypy src/tools/patient/get_patient_medications_tool.py

# Ignore specific errors (temporary)
mypy src/ --ignore-missing-imports
```

### 3. Mock Server Connection Issues

**Symptoms:**
- "Cannot connect to mock server" errors
- Tools returning empty results

**Diagnosis:**
```bash
# Check if mock server is running
curl http://localhost:8888/health

# Check mock server logs
docker logs vista-mock-server

# Restart mock server
docker-compose down && docker-compose up -d
```

**Solution:**
```bash
# Start mock server
cd mock_server
docker-compose up -d

# Wait for startup
sleep 10

# Test connection
curl http://localhost:8888/auth/token \
  -H "Content-Type: application/json" \
  -d '{"key": "test-wildcard-key-456"}'
```

### 4. Redis Port Conflicts

**Symptoms:**
- "Bind for 0.0.0.0:6379 failed: port is already allocated"
- Cache not working

**Solution:**
```bash
# This is normal - Redis is already running from mock server
# The system will automatically use the existing Redis instance
# No action needed - the error is handled gracefully

# Verify Redis is working
docker exec vista-redis redis-cli PING
```

### 5. Token Expiration Errors

**Symptoms:**
- "Authentication error" messages
- "JWT expired" errors

**Solution:**
```bash
# Check token refresh settings in .env
VISTA_TOKEN_REFRESH_BUFFER_SECONDS=30

# For production, verify API key is valid
curl -X POST https://your-vista-api.va.gov/auth/token \
  -H "Content-Type: application/json" \
  -d '{"key": "your-api-key"}'
```

### 6. Memory Issues

**Symptoms:**
- High memory usage
- Server crashes with out-of-memory errors

**Solution:**
```bash
# Check memory usage
docker stats vista-mcp-server

# Reduce cache size
echo "LOCAL_CACHE_MAX_SIZE=500" >> .env

# Restart with memory limits
docker run --memory=1g vista-mcp-server
```

## Authentication Problems

### JWT Token Issues

**Error:** `JwtException: Authentication error`

**Diagnosis:**
```bash
# Check if API key is set
echo $VISTA_API_KEY

# Test token generation
curl -X POST http://localhost:8888/auth/token \
  -H "Content-Type: application/json" \
  -d '{"key": "test-wildcard-key-456"}'
```

**Solutions:**
1. **Invalid API Key:**
   ```bash
   # Update .env with correct key
   VISTA_API_KEY=your-correct-api-key
   ```

2. **Expired Token:**
   ```bash
   # Check token refresh buffer
   VISTA_TOKEN_REFRESH_BUFFER_SECONDS=30
   ```

3. **Wrong Station/DUZ:**
   ```bash
   # Verify default values
   DEFAULT_STATION=500
   DEFAULT_DUZ=10000000219
   ```

### Permission Errors

**Error:** `SecurityFault: Access denied`

**Common Causes:**
- Insufficient permissions for the station
- Invalid DUZ (user ID)
- API key doesn't have required access

**Solutions:**
```bash
# Check user permissions
curl -X POST http://localhost:8888/vista-sites/500/users/10000000219/rpc/invoke \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "OR CPRS GUI CHART",
    "rpc": "ORWU USERINFO",
    "parameters": []
  }'

# Try different station
DEFAULT_STATION=442
```

## Connection Issues

### Vista API Connectivity

**Error:** `VistaLinkFault: Cannot connect to VistA system`

**Diagnosis:**
```bash
# Test network connectivity
ping your-vista-api.va.gov

# Test HTTPS connectivity
curl -I https://your-vista-api.va.gov

# Check DNS resolution
nslookup your-vista-api.va.gov
```

**Solutions:**
1. **Network Issues:**
   ```bash
   # Check firewall settings
   # Verify VPN connection (if required)
   # Test from different network
   ```

2. **API Endpoint Issues:**
   ```bash
   # Verify URL is correct
   VISTA_API_BASE_URL=https://your-vista-api.va.gov
   
   # Test with curl
   curl -X POST https://your-vista-api.va.gov/auth/token \
     -H "Content-Type: application/json" \
     -d '{"key": "your-api-key"}'
   ```

3. **Timeout Issues:**
   ```bash
   # Increase timeout settings
   VISTA_RPC_TIMEOUT_SECONDS=60
   ```

### Mock Server Issues

**Error:** `Connection refused` to localhost:8888

**Solutions:**
```bash
# Start mock server
cd mock_server
docker-compose up -d

# Check if port is available
netstat -tulpn | grep 8888

# Use different port
VISTA_API_BASE_URL=http://localhost:8889
```

## Performance Problems

### Slow Response Times

**Symptoms:**
- Tools taking > 30 seconds to respond
- Timeout errors

**Diagnosis:**
```bash
# Check response times in logs
grep "duration_ms" logs/octo-vista.log

# Monitor cache hit rates
docker exec vista-redis redis-cli INFO stats
```

**Solutions:**
1. **Enable Caching:**
   ```bash
   CACHE_BACKEND=local-dev-redis
   PATIENT_CACHE_TTL_MINUTES=20
   ```

2. **Optimize Queries:**
   ```bash
   # Use specific date ranges
   # Limit result sets
   # Use appropriate filters
   ```

3. **Increase Timeouts:**
   ```bash
   VISTA_RPC_TIMEOUT_SECONDS=120
   ```

### High Memory Usage

**Symptoms:**
- Memory usage > 1GB
- Server crashes

**Solutions:**
```bash
# Reduce cache size
LOCAL_CACHE_MAX_SIZE=500

# Enable cache persistence
LOCAL_CACHE_PERSISTENCE=true

# Monitor memory usage
docker stats vista-mcp-server
```

## Debug Mode

### Enabling Debug Mode

```bash
# Enable debug mode (disables data redaction)
export VISTA_MCP_DEBUG=true

# Enable verbose logging
export LOG_LEVEL=DEBUG

# Enable console logging
export ENABLE_CONSOLE_LOGGING=true

# Restart server
python run.py dev
```

**Warning:** Debug mode logs sensitive patient data. Only use in development environments.

### Debug Information

Debug mode provides:
- Detailed RPC parameters in logs
- Unmasked patient data
- Performance metrics
- Request/response details

### Disabling Debug Mode

```bash
# Disable debug mode (enables data redaction)
export VISTA_MCP_DEBUG=false

# Use production logging
export LOG_LEVEL=INFO
export ENABLE_CONSOLE_LOGGING=false
```

## Log Analysis

### Log Locations

```bash
# Main log file
logs/octo-vista.log

# Rotated logs
logs/octo-vista.log.1
logs/octo-vista.log.2

# Docker logs
docker logs vista-mcp-server
```

### Common Log Patterns

**Successful RPC Call:**
```json
{
  "timestamp": "2025-01-07T14:01:44.094714",
  "level": "INFO",
  "message": "RPC call completed: ORWU GETPATIENT",
  "rpc": "ORWU GETPATIENT",
  "station": "500",
  "duz": "10000000219",
  "success": true,
  "duration_ms": 150
}
```

**Failed RPC Call:**
```json
{
  "timestamp": "2025-01-07T14:01:44.094714",
  "level": "ERROR",
  "message": "RPC call failed: ORWU GETPATIENT",
  "rpc": "ORWU GETPATIENT",
  "station": "500",
  "duz": "10000000219",
  "success": false,
  "error": "SecurityFault: Access denied"
}
```

### Log Analysis Commands

```bash
# Find error patterns
grep -i "error\|failed\|exception" logs/octo-vista.log

# Check RPC performance
grep "duration_ms" logs/octo-vista.log | awk '{print $NF}' | sort -n

# Find authentication issues
grep -i "jwt\|auth\|token" logs/octo-vista.log

# Check cache performance
grep -i "cache" logs/octo-vista.log
```

## Error Codes Reference

### Vista API Error Types

| Error Type | Description | Common Causes | Solution |
|------------|-------------|---------------|----------|
| `SecurityFault` | Access denied | Invalid credentials, insufficient permissions | Check API key, station access |
| `VistaLinkFault` | Connection error | Network issues, server down | Check connectivity, retry |
| `RpcFault` | RPC execution failed | Invalid parameters, RPC not found | Check parameters, RPC name |
| `JwtException` | Token error | Expired/invalid token | Refresh token, check credentials |

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 401 | Unauthorized | Invalid API key, expired token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Invalid endpoint, RPC not found |
| 500 | Internal Server Error | Vista system error, configuration issue |
| 503 | Service Unavailable | Vista system down, maintenance |

### MCP-Specific Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `Tool not found` | MCP tool not registered | Check tool registration in code |
| `Invalid parameters` | Tool parameters don't match schema | Check parameter types and names |
| `Context resolution failed` | Cannot resolve station/DUZ | Check DEFAULT_STATION and DEFAULT_DUZ |

## Advanced Troubleshooting

### Network Diagnostics

```bash
# Test DNS resolution
nslookup your-vista-api.va.gov

# Test connectivity with timeout
timeout 10 curl -I https://your-vista-api.va.gov

# Check SSL certificate
openssl s_client -connect your-vista-api.va.gov:443 -servername your-vista-api.va.gov

# Test with different user agent
curl -H "User-Agent: Vista-MCP-Server/1.0" https://your-vista-api.va.gov
```

### Cache Diagnostics

```bash
# Check Redis connectivity
docker exec vista-redis redis-cli PING

# View cache contents
docker exec vista-redis redis-cli KEYS "*"

# Check cache statistics
docker exec vista-redis redis-cli INFO stats

# Clear cache
docker exec vista-redis redis-cli FLUSHDB
```

### Performance Profiling

```bash
# Monitor memory usage
docker stats vista-mcp-server

# Check CPU usage
top -p $(pgrep -f "python.*server.py")

# Profile Python code
python -m cProfile -o profile.stats server.py
```

### Configuration Validation

```bash
# Validate configuration
python -c "
from src.config import get_vista_config, get_cache_config
import json
print('Vista Config:')
print(json.dumps(get_vista_config(), indent=2))
print('\nCache Config:')
print(json.dumps(get_cache_config(), indent=2))
"

# Check environment variables
env | grep VISTA
env | grep CACHE
env | grep LOG
```

## Getting Help

### Before Asking for Help

1. **Check the logs** for error messages
2. **Enable debug mode** to get detailed information
3. **Verify configuration** with the diagnostic commands
4. **Test with mock server** to isolate issues
5. **Check this guide** for similar issues

### Information to Include

When reporting issues, include:

1. **Error messages** (exact text)
2. **Log entries** (relevant lines from logs)
3. **Configuration** (sanitized .env file)
4. **Environment** (OS, Python version, Docker version)
5. **Steps to reproduce** the issue
6. **Expected vs actual behavior**

### Debug Information Collection

```bash
# Collect debug information
echo "=== System Information ===" > debug_info.txt
uname -a >> debug_info.txt
python --version >> debug_info.txt
docker --version >> debug_info.txt

echo "=== Configuration ===" >> debug_info.txt
env | grep VISTA >> debug_info.txt
env | grep CACHE >> debug_info.txt

echo "=== Recent Logs ===" >> debug_info.txt
tail -50 logs/octo-vista.log >> debug_info.txt

echo "=== Docker Status ===" >> debug_info.txt
docker ps >> debug_info.txt
```

### Support Channels

1. **GitHub Issues** - For bugs and feature requests
2. **Documentation** - Check existing guides
3. **Test Files** - Look at test examples
4. **Mock Server** - Use for testing and development

### Common Solutions Summary

| Problem | Quick Fix |
|---------|-----------|
| Import errors | Clear Python cache |
| Connection refused | Start mock server |
| Authentication failed | Check API key |
| Slow performance | Enable caching |
| Memory issues | Reduce cache size |
| Token expired | Check refresh settings |

Remember: Most issues can be resolved by checking the logs, verifying configuration, and ensuring all services are running properly.
