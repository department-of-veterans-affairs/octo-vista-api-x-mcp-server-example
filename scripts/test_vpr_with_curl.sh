#!/bin/bash

echo "Testing VPR GET PATIENT DATA JSON RPC with mock server..."

# Test with the new format
curl -X POST http://localhost:8888/vista-api-x/vista-sites/500/users/10000000219/rpc/invoke \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: test-token" \
  -H "Cookie: JWT=test-jwt" \
  -H "X-Request-ID: test-request-123" \
  -d '{
    "context": "VPR APPLICATION PROXY",
    "rpc": "VPR GET PATIENT DATA JSON",
    "jsonResult": true,
    "parameters": [
      {
        "namedArray": {
          "patientId": "100841"
        }
      }
    ]
  }' | jq '.data.items | length'

echo ""
echo "Response items count: $(curl -s -X POST http://localhost:9000/api/v1/rpc/invoke \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: test-token" \
  -H "Cookie: JWT=test-jwt" \
  -H "X-Request-ID: test-request-123" \
  -d '{
    "context": "VPR APPLICATION PROXY", 
    "rpc": "VPR GET PATIENT DATA JSON",
    "jsonResult": true,
    "parameters": [
      {
        "namedArray": {
          "patientId": "100841"
        }
      }
    ]
  }' | jq '.data.items | length') items"

# Show item types
echo ""
echo "Item types:"
curl -s -X POST http://localhost:9000/api/v1/rpc/invoke \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: test-token" \
  -H "Cookie: JWT=test-jwt" \
  -H "X-Request-ID: test-request-123" \
  -d '{
    "context": "VPR APPLICATION PROXY",
    "rpc": "VPR GET PATIENT DATA JSON", 
    "jsonResult": true,
    "parameters": [
      {
        "namedArray": {
          "patientId": "100841"
        }
      }
    ]
  }' | jq '.data.items | group_by(.uid | split(":")[2]) | map({type: .[0].uid | split(":")[2], count: length})'