# Production Deployment Guide

This guide covers deploying the Vista API MCP Server to AWS and Azure cloud environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Options](#deployment-options)
  - [Docker](#docker)
  - [AWS ECS](#aws-ecs)
  - [Azure Container Instances](#azure-container-instances)
- [Security Considerations](#security-considerations)
- [Monitoring & Logging](#monitoring--logging)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## Overview

The Vista API MCP Server can be deployed using the HTTP transport for remote access. The server runs as a stateless container that connects to your Vista API X instance.

## Prerequisites

- Docker image built and pushed to a container registry (ECR for AWS, ACR for Azure)
- Access to Vista API X production instance
- Valid API keys and credentials
- SSL/TLS certificates for HTTPS (recommended)

## Environment Configuration

### Required Environment Variables

```env
# Vista API Configuration
VISTA_API_BASE_URL=https://your-vista-api.va.gov
VISTA_API_KEY=your-production-api-key

# Default Context
DEFAULT_STATION=500
DEFAULT_DUZ=your-default-duz

# Transport Configuration
VISTA_MCP_HTTP_HOST=0.0.0.0
VISTA_MCP_HTTP_PORT=8000

# Production Settings
VISTA_MCP_DEBUG=false
```

### Building for Production

#### AWS ECR

```bash
# Build production image
docker build -t vista-mcp-server:latest .

# Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Tag for ECR
docker tag vista-mcp-server:latest $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/vista-mcp-server:v1.0.0

# Push to ECR
docker push $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/vista-mcp-server:v1.0.0
```

#### Azure ACR

```bash
# Build production image
docker build -t vista-mcp-server:latest .

# Login to ACR
az acr login --name myregistry

# Tag for ACR
docker tag vista-mcp-server:latest myregistry.azurecr.io/vista-mcp-server:v1.0.0

# Push to ACR
docker push myregistry.azurecr.io/vista-mcp-server:v1.0.0
```

## Deployment Options

### Docker

#### Production Deployment

For production, use the standard docker-compose.yml with your production Vista API endpoint:

```bash
# Set production environment variables
export VISTA_API_BASE_URL=https://your-vista-api.va.gov
export VISTA_API_KEY=your-production-api-key

# Run the container
docker-compose up -d
```

#### Local Development with Mock Server

For local development with the Vista API X mock server:

```bash
# First, ensure the mock server is running (in the parent directory)
cd ../octo-vista-api-x
docker-compose up -d

# Then run the MCP server with dev configuration
cd ../octo-vista-api-x-mcp-server
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This will automatically connect to the mock server on the same Docker network.

#### Basic Docker deployment with SSL termination proxy:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  vista-mcp:
    image: your-registry/vista-mcp-server:v1.0.0
    container_name: vista-mcp-server
    environment:
      - VISTA_API_BASE_URL=${VISTA_API_BASE_URL}
      - VISTA_API_KEY=${VISTA_API_KEY}
      - DEFAULT_STATION=${DEFAULT_STATION}
      - DEFAULT_DUZ=${DEFAULT_DUZ}
    ports:
      - "8000:8000"
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/mcp", "-m", "1"]
      interval: 30s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: vista-mcp-nginx
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - vista-mcp
```

### AWS ECS

Task definition for ECS:

```json
{
  "family": "vista-mcp-server",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsExecutionRole",
  "networkMode": "awsvpc",
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "vista-mcp-server",
      "image": "your-registry/vista-mcp-server:v1.0.0",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "VISTA_MCP_TRANSPORT",
          "value": "http"
        }
      ],
      "secrets": [
        {
          "name": "VISTA_API_BASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:ACCOUNT:secret:vista-api-url"
        },
        {
          "name": "VISTA_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:ACCOUNT:secret:vista-api-key"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/mcp -m 1 || exit 1"],
        "interval": 30,
        "timeout": 3,
        "retries": 3
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vista-mcp-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Azure Container Instances

Deploy to Azure:

```bash
# Create resource group
az group create --name vista-mcp-rg --location eastus

# Create container instance
az container create \
  --resource-group vista-mcp-rg \
  --name vista-mcp-server \
  --image your-registry/vista-mcp-server:v1.0.0 \
  --ports 8000 \
  --environment-variables \
    DEFAULT_STATION=500 \
  --secure-environment-variables \
    VISTA_API_BASE_URL=$VISTA_API_BASE_URL \
    VISTA_API_KEY=$VISTA_API_KEY \
  --cpu 1 \
  --memory 1 \
  --restart-policy Always
```

## Security Considerations

### 1. API Key Management

- Store API keys in secure secret management systems
- Rotate keys regularly
- Use different keys for different environments

### 2. Network Security

- Always use HTTPS in production
- Implement proper CORS policies
- Use VPN or private networks when possible
- Whitelist IP addresses if applicable

### 3. SSL/TLS Configuration

Example Nginx configuration for SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://vista-mcp:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # HTTP streaming support
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

### 4. Authentication & Authorization

- Implement OAuth2 or JWT authentication if needed
- Use API Gateway for additional security layers
- Monitor and log all access attempts

## Monitoring & Logging

### 1. Health Checks

Monitor the `/mcp` endpoint for availability:

```bash
# Health check script
curl -f https://mcp.yourdomain.com/mcp \
  -H "Accept: text/event-stream" \
  -m 5 \
  --write-out "%{http_code}" \
  --silent \
  --output /dev/null
```

### 2. Metrics to Monitor

- Response time for HTTP connections
- Number of active sessions
- Error rates
- Memory and CPU usage
- Vista API connection status

### 3. Logging

Configure structured logging:

```python
# In production, ensure logs are structured
VISTA_MCP_DEBUG=false  # Reduce log verbosity
```

### 4. Cloud Monitoring Solutions

#### AWS CloudWatch

```bash
# Enable CloudWatch Container Insights for ECS
aws ecs put-account-setting \
  --name containerInsights \
  --value enabled

# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name vista-mcp-monitoring \
  --dashboard-body file://cloudwatch-dashboard.json
```

#### Azure Monitor

```bash
# Enable monitoring for Container Instances
az monitor log-analytics workspace create \
  --resource-group vista-mcp-rg \
  --workspace-name vista-mcp-logs

# Configure container group with Log Analytics
az container create \
  --resource-group vista-mcp-rg \
  --name vista-mcp-server \
  --log-analytics-workspace vista-mcp-logs \
  --log-analytics-workspace-key $WORKSPACE_KEY
```

## Scaling

### Horizontal Scaling

The HTTP server is stateless and can be scaled horizontally:

1. **Load Balancer Configuration**
   - Use load balancing for HTTP connections
   - Configure appropriate timeouts (> 60s)

2. **Auto-scaling Rules**
   - Scale based on CPU usage (target 70%)
   - Scale based on memory usage (target 80%)
   - Scale based on connection count

### Example Auto-scaling (AWS ECS)

```json
{
  "targetCapacity": 10,
  "minimumHealthyPercent": 100,
  "maximumPercent": 200,
  "scalableTargetConfig": {
    "minCapacity": 2,
    "maxCapacity": 10,
    "targetTrackingScalingPolicies": [
      {
        "targetValue": 70.0,
        "predefinedMetricSpecification": {
          "predefinedMetricType": "ECSServiceAverageCPUUtilization"
        }
      },
      {
        "targetValue": 80.0,
        "predefinedMetricSpecification": {
          "predefinedMetricType": "ECSServiceAverageMemoryUtilization"
        }
      }
    ]
  }
}
```

### Example Auto-scaling (Azure Container Instances)

For Azure, use Azure Container Apps for auto-scaling:

```bash
az containerapp create \
  --name vista-mcp-server \
  --resource-group vista-mcp-rg \
  --image your-registry/vista-mcp-server:v1.0.0 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 2 \
  --max-replicas 10 \
  --scale-rule-name cpu-scaling \
  --scale-rule-type http \
  --scale-rule-http-concurrency 100 \
  --environment-variables \
    DEFAULT_STATION=500 \
  --secrets \
    vista-api-url="$VISTA_API_BASE_URL" \
    vista-api-key="$VISTA_API_KEY"
```

## Troubleshooting

### Common Issues

1. **HTTP Connection Issues**
   - Check proxy/load balancer timeout settings
   - Ensure keep-alive is enabled
   - Monitor network stability

2. **High Memory Usage**
   - Monitor active session count
   - Implement session cleanup
   - Check for memory leaks

3. **Vista API Connection Issues**
   - Verify network connectivity
   - Check API key validity
   - Monitor Vista API status

### Debug Mode

For troubleshooting, temporarily enable debug mode:

```bash
# AWS ECR
docker run -e VISTA_MCP_DEBUG=true $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/vista-mcp-server:v1.0.0

# Azure ACR
docker run -e VISTA_MCP_DEBUG=true myregistry.azurecr.io/vista-mcp-server:v1.0.0
```

### Performance Tuning

1. **Connection Pooling**
   - Reuse Vista API connections
   - Implement connection limits

2. **Caching**
   - Cache frequently accessed data
   - Use Redis for distributed caching

3. **Resource Limits**
   - Set appropriate memory limits
   - Configure connection limits
   - Implement rate limiting

## Production Checklist

- [ ] SSL/TLS certificates configured
- [ ] API keys stored securely
- [ ] Health checks configured
- [ ] Monitoring and alerting set up
- [ ] Logging configured and centralized
- [ ] Backup and disaster recovery plan
- [ ] Auto-scaling configured
- [ ] Security scanning enabled
- [ ] Load testing completed
- [ ] Documentation updated

## Support

For production issues:
1. Check container logs
2. Verify Vista API connectivity
3. Review monitoring dashboards
4. Contact Vista API X support if needed