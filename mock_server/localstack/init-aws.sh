#!/bin/bash

echo "Initializing LocalStack DynamoDB..."

# Wait for LocalStack to be ready
sleep 5

# Create the AUTH_APPLICATIONS table
awslocal dynamodb create-table \
    --table-name AUTH_APPLICATIONS_TABLE_NAME \
    --attribute-definitions \
        AttributeName=appKey,AttributeType=S \
    --key-schema \
        AttributeName=appKey,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1

echo "DynamoDB table created successfully"

# Load test data for standard key
awslocal dynamodb put-item \
    --table-name AUTH_APPLICATIONS_TABLE_NAME \
    --item file:///etc/localstack/init/ready.d/dynamodb-seed.json \
    --region us-east-1

# Load test data for wildcard key
awslocal dynamodb put-item \
    --table-name AUTH_APPLICATIONS_TABLE_NAME \
    --item file:///etc/localstack/init/ready.d/dynamodb-seed-wildcard.json \
    --region us-east-1

# Load test data for limited key
awslocal dynamodb put-item \
    --table-name AUTH_APPLICATIONS_TABLE_NAME \
    --item file:///etc/localstack/init/ready.d/dynamodb-seed-limited.json \
    --region us-east-1

echo "Test data loaded successfully"