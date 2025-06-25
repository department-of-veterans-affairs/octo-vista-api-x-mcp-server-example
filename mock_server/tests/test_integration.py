"""
Integration tests for Vista API X Mock Server
"""

import pytest
import httpx
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8080/vista-api-x"
TEST_API_KEY = "test-standard-key-123"
TEST_STATION = "500"
TEST_DUZ = "10000000219"


@pytest.fixture
async def client():
    """Create test client"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        yield client


@pytest.fixture
async def auth_token(client):
    """Get authentication token"""
    response = await client.post(
        "/auth/token",
        json={"key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["token"]


@pytest.mark.asyncio
async def test_auth_token_generation(client):
    """Test JWT token generation"""
    response = await client.post(
        "/auth/token",
        json={"key": TEST_API_KEY}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "token" in data["data"]
    assert data["path"] == "/auth/token"


@pytest.mark.asyncio
async def test_auth_token_invalid_key(client):
    """Test invalid API key"""
    response = await client.post(
        "/auth/token",
        json={"key": "invalid-key"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["errorCode"] == "JWT-AUTHENTICATION-ERROR-0002"


@pytest.mark.asyncio
async def test_token_refresh(client, auth_token):
    """Test token refresh"""
    response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "token" in data["data"]
    assert data["path"] == "/auth/refresh"


@pytest.mark.asyncio
async def test_rpc_patient_list(client, auth_token):
    """Test ORWPT LIST RPC"""
    response = await client.post(
        f"/vista-sites/{TEST_STATION}/users/{TEST_DUZ}/rpc/invoke",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "context": "OR CPRS GUI CHART",
            "rpc": "ORWPT LIST",
            "parameters": [{"string": "^A"}]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "payload" in data
    assert "result" in data["payload"]
    
    # Check result format (delimited string)
    result = data["payload"]["result"]
    assert "^" in result  # Should contain delimited data


@pytest.mark.asyncio
async def test_rpc_vpr_patient_data(client, auth_token):
    """Test VPR GET PATIENT DATA JSON RPC"""
    response = await client.post(
        f"/vista-sites/{TEST_STATION}/users/{TEST_DUZ}/rpc/invoke",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "context": "VPR APPLICATION PROXY",
            "rpc": "VPR GET PATIENT DATA JSON",
            "jsonResult": True,
            "parameters": [
                {"string": "100022"},  # Patient DFN
                {"string": ""},         # Start date
                {"string": ""},         # End date
                {"string": "patient;vital;med"}  # Domains
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "payload" in data
    
    # Should return JSON object directly
    payload = data["payload"]
    assert "data" in payload
    assert "items" in payload["data"]


@pytest.mark.asyncio
async def test_rpc_unauthorized_station(client, auth_token):
    """Test RPC with unauthorized station"""
    response = await client.post(
        "/vista-sites/999/users/99999/rpc/invoke",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "context": "OR CPRS GUI CHART",
            "rpc": "ORWPT LIST",
            "parameters": []
        }
    )
    
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "ACCESS-DENIED" in data["errorCode"]


@pytest.mark.asyncio
async def test_rpc_missing_auth(client):
    """Test RPC without authentication"""
    response = await client.post(
        f"/vista-sites/{TEST_STATION}/users/{TEST_DUZ}/rpc/invoke",
        json={
            "context": "OR CPRS GUI CHART",
            "rpc": "ORWPT LIST",
            "parameters": []
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["errorCode"] == "JWT-ACCESS-DENIED-0001"


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "dependencies" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data