#!/bin/bash

echo "🚀 Vista API X Mock Server Setup"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Generate RSA keys if they don't exist
if [ ! -f "keys/private_key.pem" ]; then
    echo "🔐 Generating RSA keys..."
    python3 scripts/generate_rsa_keys.py
    echo "✅ RSA keys generated"
else
    echo "✅ RSA keys already exist"
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to initialize..."
for i in {1..30}; do
    if docker exec vista-localstack awslocal dynamodb list-tables --region us-east-1 > /dev/null 2>&1; then
        echo "✅ LocalStack is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ LocalStack failed to start properly"
        exit 1
    fi
    sleep 2
done

# Check if table already exists
if docker exec vista-localstack awslocal dynamodb describe-table --table-name AUTH_APPLICATIONS_TABLE_NAME --region us-east-1 > /dev/null 2>&1; then
    echo "✅ Database table already exists"
else
    echo "📊 Creating DynamoDB table..."
    docker exec vista-localstack awslocal dynamodb create-table \
        --table-name AUTH_APPLICATIONS_TABLE_NAME \
        --attribute-definitions AttributeName=appKey,AttributeType=S \
        --key-schema AttributeName=appKey,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --region us-east-1 > /dev/null
    
    echo "📝 Loading test data..."
    docker exec vista-localstack awslocal dynamodb put-item \
        --table-name AUTH_APPLICATIONS_TABLE_NAME \
        --item file:///etc/localstack/init/ready.d/dynamodb-seed.json \
        --region us-east-1
    
    docker exec vista-localstack awslocal dynamodb put-item \
        --table-name AUTH_APPLICATIONS_TABLE_NAME \
        --item file:///etc/localstack/init/ready.d/dynamodb-seed-wildcard.json \
        --region us-east-1
    
    docker exec vista-localstack awslocal dynamodb put-item \
        --table-name AUTH_APPLICATIONS_TABLE_NAME \
        --item file:///etc/localstack/init/ready.d/dynamodb-seed-limited.json \
        --region us-east-1
    
    echo "✅ Database initialized"
fi

# Wait for Vista mock to be ready
echo "⏳ Waiting for Vista API X Mock to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8080/ > /dev/null 2>&1; then
        echo "✅ Vista API X Mock is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Vista API X Mock failed to start properly"
        exit 1
    fi
    sleep 2
done

# Test authentication
echo "🔍 Testing authentication..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/auth/token \
    -H "Content-Type: application/json" \
    -d '{"key": "test-standard-key-123"}')

if echo "$TOKEN_RESPONSE" | grep -q '"token"'; then
    echo "✅ Authentication test successful"
else
    echo "❌ Authentication test failed"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Vista API X Mock Server is running."
echo ""
echo "📋 Quick Test Commands:"
echo ""
echo "# Get a token:"
echo "curl -X POST http://localhost:8080/auth/token \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"key\": \"test-standard-key-123\"}'"
echo ""
echo "# Make an RPC call (replace TOKEN with actual token):"
echo "curl -X POST http://localhost:8080/vista-sites/500/users/10000000219/rpc/invoke \\"
echo "  -H \"Authorization: Bearer TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"context\": \"OR CPRS GUI CHART\","
echo "    \"rpc\": \"ORWPT LIST\","
echo "    \"parameters\": [{\"string\": \"^SMITH\"}]"
echo "  }'"
echo ""
echo "📝 Available API Keys:"
echo "• test-standard-key-123 - Standard access"
echo "• test-wildcard-key-456 - Full access"
echo "• test-limited-key-789  - Limited access"
echo ""
echo "🌐 Endpoints:"
echo "• API: http://localhost:8080"
echo "• API Docs: http://localhost:8080/docs"
echo "• Health: http://localhost:9990/health"
echo "• DynamoDB UI: http://localhost:8001"
echo "• LocalStack: http://localhost:4566"