# Redis Configuration and Testing

## Overview

Redis is configured as the production cache backend for the MCP server to handle patient data caching at scale. The setup includes:

- Redis 7 Alpine (lightweight, production-ready)
- Persistent storage with AOF (Append Only File)
- Memory limit of 256MB with LRU eviction
- Connection pooling for performance
- JSON serialization for complex data structures

## Quick Start

### 1. Start Redis

Using Docker Compose (recommended):
```bash
docker-compose up -d redis
```

Or run Redis locally:
```bash
# macOS with Homebrew
brew services start redis

# Linux
redis-server

# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Test Redis Configuration

Run the test script:
```bash
python scripts/test_redis.py
```

This will verify:
- Redis connectivity
- Basic operations (get/set/delete)
- Patient data caching
- Cache factory configuration

### 3. Configure MCP Server

Set environment variables:
```bash
# Use Redis as cache backend
export CACHE_BACKEND=redis

# Optional: Custom Redis URL (default: redis://localhost:6379/0)
export REDIS_URL=redis://localhost:6379/0

# Optional: Cache TTL in minutes (default: 10)
export PATIENT_CACHE_TTL_MINUTES=10
```

## Architecture

### Cache Key Pattern

Patient data is cached with user-scoped keys:
```
patient:v1:{station}:{dfn}:{user_duz}
```

Example: `patient:v1:500:100841:10000000219`

### Data Flow

1. Patient tool requests data
2. Check Redis cache first
3. If miss, fetch from VistA via RPC
4. Store in Redis with 10-minute TTL
5. Return data to tool

### Redis Configuration

The Docker Compose configuration includes:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

- `--appendonly yes`: Enables persistence
- `--maxmemory 256mb`: Memory limit
- `--maxmemory-policy allkeys-lru`: Evicts least recently used keys when memory is full

## Monitoring

### Check Redis Status

```bash
# Connect to Redis CLI
docker exec -it vista-mcp-redis redis-cli

# Check memory usage
INFO memory

# Monitor commands in real-time
MONITOR

# List all MCP keys
KEYS mcp:*

# Check specific patient cache
GET "mcp:patient:v1:500:100841:10000000219"
```

### Cache Hit Rate

Monitor cache effectiveness:
```bash
# In Redis CLI
INFO stats
# Look for keyspace_hits and keyspace_misses
```

## Troubleshooting

### Redis Connection Failed

1. Check if Redis is running:
   ```bash
   docker ps | grep redis
   # or
   redis-cli ping
   ```

2. Check Redis logs:
   ```bash
   docker logs vista-mcp-redis
   ```

3. Verify network connectivity:
   ```bash
   telnet localhost 6379
   ```

### Cache Not Working

1. Verify environment variable:
   ```bash
   echo $CACHE_BACKEND
   # Should be: redis
   ```

2. Check Redis connection in MCP logs:
   ```bash
   # Look for Redis-related messages
   mise run dev 2>&1 | grep -i redis
   ```

3. Test with the test script:
   ```bash
   CACHE_BACKEND=redis python scripts/test_redis.py
   ```

### Memory Issues

If Redis runs out of memory:

1. Check current usage:
   ```bash
   docker exec -it vista-mcp-redis redis-cli INFO memory
   ```

2. Flush all data if needed:
   ```bash
   docker exec -it vista-mcp-redis redis-cli FLUSHALL
   ```

3. Increase memory limit in docker-compose.yml:
   ```yaml
   command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

## Production Considerations

### Security

1. **Authentication**: Add Redis password
   ```yaml
   command: redis-server --requirepass yourpassword --appendonly yes
   ```

2. **Network**: Bind to specific interface
   ```yaml
   command: redis-server --bind 127.0.0.1 --appendonly yes
   ```

3. **Encryption**: Use TLS for connections
   ```bash
   export REDIS_URL=rediss://user:password@host:6380/0
   ```

### High Availability

Consider Redis Sentinel or Redis Cluster for:
- Automatic failover
- Read replicas
- Horizontal scaling

### Backup

Backup Redis data directory:
```bash
# Docker volume backup
docker run --rm -v vista-mcp-redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data

# Restore
docker run --rm -v vista-mcp-redis-data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /
```

## Performance Tips

1. **Connection Pooling**: Already configured in RedisCacheBackend
2. **Pipeline Commands**: For bulk operations
3. **Compression**: For large patient records
4. **Partial Updates**: Update only changed fields

## Development vs Production

| Aspect | Development | Production |
|--------|------------|------------|
| Backend | Memory (no Redis needed) | Redis |
| Persistence | None | AOF enabled |
| Memory Limit | Unlimited | 256MB+ |
| Eviction | Manual clear | LRU automatic |
| Monitoring | Basic logs | Full metrics |