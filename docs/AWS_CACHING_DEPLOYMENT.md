# AWS Caching Deployment Guide

This guide covers deploying and configuring AWS-managed caching solutions for the Vista API MCP Server to improve scalability, reliability, and performance in production environments.

## Overview

The new caching system replaces the in-memory cache with AWS-managed services:

- **ElastiCache for Redis**: Primary caching layer with high performance
- **ElastiCache for Memcached**: Alternative caching engine for specific use cases
- **DynamoDB Accelerator (DAX)**: For frequently accessed data with DynamoDB
- **Multi-tier caching**: Hierarchical caching with automatic failover

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Server   │───▶│  ElastiCache     │───▶│   Redis/Mem     │
│                 │    │  (Primary)       │    │   Cluster       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │              ┌──────────────────┐
         │              │  Multi-tier      │
         │              │  Cache Layer     │
         │              └──────────────────┘
         │                       │
         │              ┌──────────────────┐
         └──────────────▶│  Redis/DAX      │
                        │  (Fallback)      │
                        └──────────────────┘
```

## Prerequisites

- AWS account with appropriate permissions
- VPC configuration for ElastiCache access
- IAM roles for service access
- Network security group configuration

## 1. ElastiCache for Redis Setup

### 1.1 Create ElastiCache Subnet Group

```bash
aws elasticache create-subnet-group \
    --subnet-group-name vista-cache-subnet-group \
    --subnet-ids subnet-12345678 subnet-87654321 \
    --description "Subnet group for Vista API cache"
```

### 1.2 Create Security Group

```bash
aws ec2 create-security-group \
    --group-name vista-cache-sg \
    --description "Security group for Vista API cache" \
    --vpc-id vpc-12345678

# Allow inbound Redis traffic from MCP server
aws ec2 authorize-security-group-ingress \
    --group-id sg-12345678 \
    --protocol tcp \
    --port 6379 \
    --source-group sg-mcp-server-sg
```

### 1.3 Create ElastiCache Cluster

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id vista-cache-cluster \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1 \
    --cache-subnet-group-name vista-cache-subnet-group \
    --security-group-ids sg-12345678 \
    --port 6379 \
    --preferred-availability-zone us-east-1a
```

### 1.4 Configure Authentication (Optional)

```bash
# Create auth token
aws elasticache create-user \
    --user-id vista-cache-user \
    --user-name vista-cache-user \
    --passwords "YourSecurePassword123!" \
    --engine redis \
    --access-string "on ~* +@all"

# Create user group
aws elasticache create-user-group \
    --user-group-id vista-cache-group \
    --engine redis \
    --user-ids vista-cache-user
```

## 2. ElastiCache for Memcached Setup

### 2.1 Create Memcached Cluster

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id vista-memcached-cluster \
    --engine memcached \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1 \
    --cache-subnet-group-name vista-cache-subnet-group \
    --security-group-ids sg-12345678 \
    --port 11211 \
    --preferred-availability-zone us-east-1a
```

## 3. DynamoDB Accelerator (DAX) Setup

### 3.1 Create DynamoDB Table

```bash
aws dynamodb create-table \
    --table-name vista_cache \
    --attribute-definitions AttributeName=cache_key,AttributeType=S \
    --key-schema AttributeName=cache_key,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Enable TTL
aws dynamodb update-time-to-live \
    --table-name vista_cache \
    --time-to-live-specification Enabled=true,AttributeName=expires_at
```

### 3.2 Create DAX Cluster

```bash
aws dax create-cluster \
    --cluster-name vista-dax-cluster \
    --node-type dax.t3.small \
    --replication-factor 1 \
    --subnet-group-name vista-cache-subnet-group \
    --security-group-ids sg-12345678 \
    --iam-role-arn arn:aws:iam::123456789012:role/DAXServiceRole
```

## 4. Environment Configuration

### 4.1 Basic ElastiCache Configuration

```bash
# .env file
CACHE_BACKEND=elasticache
AWS_CACHE_BACKEND=elasticache
ELASTICACHE_ENDPOINT=your-cluster.xxxxx.cache.amazonaws.com
ELASTICACHE_PORT=6379
ELASTICACHE_AUTH_TOKEN=your-auth-token
AWS_REGION=us-east-1
CACHE_KEY_PREFIX=mcp:

# Updated TTL settings
PATIENT_CACHE_TTL_MINUTES=20
TOKEN_CACHE_TTL_MINUTES=55
RESPONSE_CACHE_TTL_MINUTES=10
```

### 4.2 Multi-tier Configuration

```bash
# .env file
CACHE_BACKEND=multi-tier
AWS_CACHE_BACKEND=elasticache

# ElastiCache (fastest tier)
ELASTICACHE_ENDPOINT=your-cluster.xxxxx.cache.amazonaws.com
ELASTICACHE_PORT=6379

# Memcached (second tier)
MEMCACHED_ENDPOINT=your-memcached-cluster.xxxxx.cache.amazonaws.com
MEMCACHED_PORT=11211

# DAX (third tier)
DAX_ENDPOINT=your-dax-cluster.xxxxx.dax-clusters.amazonaws.com
DAX_TABLE_NAME=vista_cache

# Multi-tier behavior
MULTI_TIER_WRITE_THROUGH=true
MULTI_TIER_READ_THROUGH=true
```

## 5. IAM Configuration

### 5.1 Create IAM Role for MCP Server

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticache:DescribeCacheClusters",
                "elasticache:DescribeCacheNodes",
                "dax:DescribeClusters",
                "dax:DescribeNodes",
                "dynamodb:DescribeTable",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:Scan"
            ],
            "Resource": "*"
        }
    ]
}
```

### 5.2 Attach to ECS Task Role

```bash
aws iam attach-role-policy \
    --role-name ecsTaskRole \
    --policy-arn arn:aws:iam::123456789012:policy/VistaCachePolicy
```

## 6. Network Configuration

### 6.1 VPC Configuration

```bash
# Create VPC for caching services
aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --enable-dns-hostnames \
    --enable-dns-support

# Create subnets in different AZs
aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a

aws ec2 create-subnet \
    --vpc-id vpc-12345678 \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b
```

### 6.2 Security Group Rules

```bash
# Allow MCP server to access cache
aws ec2 authorize-security-group-ingress \
    --group-id sg-cache-sg \
    --protocol tcp \
    --port 6379 \
    --source-group sg-mcp-server-sg

# Allow MCP server to access Memcached
aws ec2 authorize-security-group-ingress \
    --group-id sg-cache-sg \
    --protocol tcp \
    --port 11211 \
    --source-group sg-mcp-server-sg
```

## 7. Monitoring and Health Checks

### 7.1 CloudWatch Metrics

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name VistaCacheDashboard \
    --dashboard-body file://cache-dashboard.json
```

### 7.2 Health Check Endpoint

```python
# Example health check endpoint
@app.get("/health/cache")
async def cache_health():
    cache_factory = CacheFactory()
    backend = await cache_factory.create_backend()
    
    if hasattr(backend, 'get_tier_health'):
        health = await backend.get_tier_health()
    else:
        health = {
            "status": "healthy" if await backend.ping() else "unhealthy",
            "backend_type": backend.__class__.__name__
        }
    
    return health
```

## 8. Performance Tuning

### 8.1 ElastiCache Optimization

```bash
# Configure parameter groups
aws elasticache create-cache-parameter-group \
    --cache-parameter-group-name vista-optimized \
    --cache-parameter-group-family redis6.x \
    --description "Optimized parameters for Vista API"

# Set memory policy
aws elasticache modify-cache-parameter-group \
    --cache-parameter-group-name vista-optimized \
    --parameter-name-values ParameterName=maxmemory-policy,ParameterValue=allkeys-lru
```

### 8.2 Connection Pooling

```python
# Configure connection pool settings
ELASTICACHE_CONNECTION_POOL = {
    "max_connections": 20,
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
}
```

## 9. Backup and Recovery

### 9.1 ElastiCache Snapshots

```bash
# Create manual snapshot
aws elasticache create-snapshot \
    --snapshot-name vista-cache-backup-$(date +%Y%m%d) \
    --cache-cluster-id vista-cache-cluster

# Enable automatic snapshots
aws elasticache modify-cache-cluster \
    --cache-cluster-id vista-cache-cluster \
    --snapshot-retention-limit 7 \
    --snapshot-window 03:00-04:00
```

### 9.2 DAX Backup

```bash
# DAX automatically backs up to S3
aws dax describe-clusters \
    --cluster-names vista-dax-cluster
```

## 10. Cost Optimization

### 10.1 Reserved Instances

```bash
# Purchase reserved instances for predictable workloads
aws elasticache describe-reserved-cache-nodes-offerings \
    --cache-node-type cache.t3.micro \
    --product-description "ElastiCache for Redis"
```

### 10.2 Auto Scaling

```bash
# Configure auto scaling for variable workloads
aws application-autoscaling register-scalable-target \
    --service-namespace elasticache \
    --scalable-dimension elasticache:replication-group:NodeGroups \
    --resource-id replication-group/vista-cache-cluster \
    --min-capacity 1 \
    --max-capacity 5
```

## 11. Troubleshooting

### 11.1 Common Issues

1. **Connection Timeouts**: Check security groups and VPC routing
2. **Authentication Failures**: Verify auth tokens and IAM permissions
3. **Performance Issues**: Monitor CloudWatch metrics and adjust node types
4. **Memory Pressure**: Configure eviction policies and monitor memory usage

### 11.2 Debug Commands

```bash
# Test ElastiCache connection
redis-cli -h your-cluster.xxxxx.cache.amazonaws.com -p 6379 ping

# Test Memcached connection
telnet your-memcached-cluster.xxxxx.cache.amazonaws.com 11211

# Check DAX cluster status
aws dax describe-clusters --cluster-names vista-dax-cluster
```

## 12. Migration from In-Memory Cache

### 12.1 Gradual Migration

1. Deploy with both in-memory and AWS caching
2. Monitor performance and reliability
3. Gradually shift traffic to AWS services
4. Remove in-memory cache once stable

### 12.2 Data Migration

```python
# Example migration script
async def migrate_cache_data():
    old_cache = MemoryCacheBackend()
    new_cache = await CacheFactory.create_backend()
    
    # Migrate existing data
    # Note: This is a simplified example
    # In practice, you'd need to handle the specific data structure
    pass
```

## 13. Best Practices

1. **Use Multi-tier Caching**: Combine fast and persistent layers
2. **Implement Circuit Breakers**: Handle cache failures gracefully
3. **Monitor Cache Hit Rates**: Optimize TTL based on usage patterns
4. **Use Consistent Hashing**: For distributed caching scenarios
5. **Implement Cache Warming**: Pre-populate frequently accessed data
6. **Regular Health Checks**: Monitor cache cluster health
7. **Backup Strategies**: Implement automated backup and recovery
8. **Security**: Use VPC, security groups, and IAM roles

## 14. Security Considerations

1. **Network Isolation**: Use private subnets for cache clusters
2. **Encryption**: Enable encryption at rest and in transit
3. **Access Control**: Use IAM roles and security groups
4. **Audit Logging**: Enable CloudTrail for API calls
5. **Regular Updates**: Keep cache engines updated

## 15. Support and Resources

- [ElastiCache Documentation](https://docs.aws.amazon.com/elasticache/)
- [DAX Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html)
- [AWS Support](https://aws.amazon.com/support/)
- [Vista API MCP Server Issues](https://github.com/your-org/vista-api-mcp-server/issues)
