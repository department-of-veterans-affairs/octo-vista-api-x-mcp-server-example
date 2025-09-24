# Local Development Cache Setup

This guide covers setting up and using caching for local development of the Vista API MCP Server.

## Overview

The MCP server uses caching to improve performance by storing:
- Patient data (20-minute TTL)
- JWT authentication tokens (55-minute TTL)
- Other API responses (10-minute TTL)

## Quick Start

### Option 1: Automatic Setup with Mock Server (Recommended)

The easiest way to use caching is with the mock server, which includes Redis and monitoring tools:

```bash
# Using Python (universal)
python run.py dev-with-mock-and-redis

# Using mise (Mac/Linux)
mise run dev-with-mock-and-redis
```

This automatically:
- Starts Redis container on port 6379
- Configures all cache environment variables
- Starts Redis Commander UI at http://localhost:8002
- Uses optimal cache settings for development

### Option 2: Manual Redis Setup

If you need Redis without the mock server:

```bash
# Start Redis container
docker run -d -p 6379:6379 --name my-redis redis:alpine

# Configure environment
export CACHE_BACKEND=local-dev-redis
export LOCAL_REDIS_URL=redis://localhost:6379
export LOCAL_REDIS_FALLBACK=true

# Run the server
python run.py dev
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Cache Backend Selection
CACHE_BACKEND=memory                    # Default: in-memory cache
# CACHE_BACKEND=local-dev-redis         # Use local Redis
# CACHE_BACKEND=redis                   # Production Redis
# CACHE_BACKEND=elasticache             # AWS ElastiCache

# Local Redis Configuration
LOCAL_CACHE_BACKEND_TYPE=elasticache    # Redis interface type
LOCAL_REDIS_URL=redis://localhost:6379  # Redis connection URL
LOCAL_REDIS_PASSWORD=                   # Redis password (if required)
LOCAL_REDIS_FALLBACK=true              # Fallback to memory if Redis fails

# Cache TTL Settings (in minutes)
PATIENT_CACHE_TTL_MINUTES=20           # Patient data cache duration
TOKEN_CACHE_TTL_MINUTES=55             # JWT token cache duration
RESPONSE_CACHE_TTL_MINUTES=10          # Other responses cache duration

# Cache Key Configuration
CACHE_KEY_PREFIX=mcp:                  # Prefix for all cache keys

# In-Memory Cache Settings
LOCAL_CACHE_MAX_SIZE=1000              # Max items in memory cache
LOCAL_CACHE_PERSISTENCE=false          # Persist cache to disk
LOCAL_CACHE_PERSISTENCE_FILE=local_cache.json  # Persistence file path
```

## Cache Backends

### Memory Cache (Default)

- No setup required
- Fast for development
- Data lost on restart
- Limited by application memory

### Local Redis

- Persistent across restarts
- Shared between multiple server instances
- Supports advanced features (TTL, eviction policies)
- Requires Docker

### Production Backends

For production deployments, see [AWS_CACHING_DEPLOYMENT.md](AWS_CACHING_DEPLOYMENT.md) for:
- AWS ElastiCache setup
- DynamoDB Accelerator (DAX)
- Multi-tier caching

## Monitoring and Management

### Redis Commander UI

When using `dev-with-mock-and-redis`, access the web UI at http://localhost:8002

Features:
- Browse all cached keys in tree view
- View cached JSON data formatted
- Monitor TTL for each key
- Search and filter keys
- Manual cache management

### Command-Line Tools

```bash
# List all cached keys
docker exec vista-redis redis-cli KEYS "*"

# View specific patient data
docker exec vista-redis redis-cli GET "mcp:patient:v1:500:ICN:DUZ"

# Check remaining TTL (in seconds)
docker exec vista-redis redis-cli TTL "mcp:patient:v1:500:ICN:DUZ"

# Monitor all Redis commands in real-time
docker exec -it vista-redis redis-cli MONITOR

# Get cache statistics
docker exec vista-redis redis-cli INFO stats

# Clear all cache (careful!)
docker exec vista-redis redis-cli FLUSHDB
```

## Cache Key Structure

Cache keys follow this pattern:

```
{prefix}:{type}:{version}:{station}:{identifier}:{user}
```

Example:
```
mcp:patient:v1:500:1000220000V123456:10000000219
│   │       │  │   │                 │
│   │       │  │   │                 └─ User DUZ
│   │       │  │   └─────────────────── Patient ICN
│   │       │  └─────────────────────── Station number
│   │       └────────────────────────── Cache version
│   └────────────────────────────────── Data type
└────────────────────────────────────── Prefix (configurable)
```

## Testing Cache

### Verify Cache is Working

```python
python -c "
from src.services.cache.factory import CacheFactory
import asyncio

async def test():
    cache = await CacheFactory.create_patient_cache()
    print(f'Cache backend: {type(cache).__name__}')

    # Test set and get
    await cache.set_patient_data('500', 'test-icn', 'test-duz', {'test': 'data'})
    data = await cache.get_patient_data('500', 'test-icn', 'test-duz')
    print(f'Cache working: {data is not None}')

    # Check TTL
    import redis
    r = redis.Redis(host='localhost', port=6379)
    ttl = r.ttl('mcp:patient:v1:500:test-icn:test-duz')
    print(f'TTL remaining: {ttl} seconds')

asyncio.run(test())
"
```

### Performance Testing

```bash
# Test cache hit rate
for i in {1..10}; do
    time python -c "
from src.tools.patient import get_patient_medications
import asyncio
asyncio.run(get_patient_medications.execute({
    'patient_icn': '1000220000V123456'
}))
"
done

# First call: ~500ms (cache miss)
# Subsequent calls: ~50ms (cache hit)
```

## Troubleshooting

### Issue: "Port 6379 already allocated"

**Symptom**: Error message when starting local cache
**Cause**: Redis is already running (likely from mock server)
**Solution**: This is handled automatically - the system uses the existing Redis instance

### Issue: Cache not persisting

**Symptom**: Cache cleared after restart
**Check**:
```bash
docker ps | grep redis  # Verify Redis is running
docker logs vista-redis # Check for errors
```

### Issue: High memory usage

**Solution**: Adjust cache settings
```bash
# Reduce cache size
export LOCAL_CACHE_MAX_SIZE=100

# Reduce TTL
export PATIENT_CACHE_TTL_MINUTES=5
```

### Issue: Can't connect to Redis

**Debug steps**:
1. Check Redis is running: `docker ps | grep redis`
2. Test connection: `docker exec vista-redis redis-cli ping`
3. Check network: `telnet localhost 6379`
4. Review logs: `docker logs vista-redis`

## Best Practices

1. **Development**: Use `dev-with-mock-and-redis` for consistent setup
2. **Testing**: Clear cache between test runs with `docker exec vista-redis redis-cli FLUSHDB`
3. **Debugging**: Use Redis Commander UI to inspect cached data
4. **Performance**: Monitor cache hit rates with `docker exec vista-redis redis-cli INFO stats`
5. **Security**: Never cache sensitive data without proper TTL

## Docker Compose Integration

The mock server's `docker-compose.yml` includes:

```yaml
redis:
  image: redis:7-alpine
  container_name: vista-redis
  ports:
    - "6379:6379"
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s

redis-commander:
  image: rediscommander/redis-commander:latest
  container_name: vista-redis-commander
  ports:
    - "8002:8081"
  environment:
    - REDIS_HOSTS=local:redis:6379
  depends_on:
    - redis
```

## Related Documentation

- [DEVELOPMENT.md](DEVELOPMENT.md) - General development guide
- [AWS_CACHING_DEPLOYMENT.md](AWS_CACHING_DEPLOYMENT.md) - Production cache setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide