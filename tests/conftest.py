"""Pytest configuration and shared fixtures"""

from unittest.mock import AsyncMock, Mock

import pytest
from mcp.server.fastmcp import FastMCP

from src.vista.base import BaseVistaClient


@pytest.fixture
def mock_vista_client():
    """Create a mock Vista client for testing"""
    client = Mock(spec=BaseVistaClient)
    client.invoke_rpc = AsyncMock()
    client.with_fresh_token = AsyncMock(return_value=client)
    return client


@pytest.fixture
def mcp_server():
    """Create an MCP server instance for testing"""
    return FastMCP(name="Test Server", version="1.0.0", description="Test server")


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "demographics": {
            "fullName": "TEST,PATIENT",
            "familyName": "TEST",
            "givenNames": ["PATIENT"],
            "ssn": "666001234",
            "dateOfBirth": "1980-01-01",
            "genderCode": "M",
            "genderName": "MALE",
            "icn": "1234567890V123456",
        },
        "vital_signs": [
            {
                "uid": "urn:va:vital:500:100:1",
                "localId": "1",
                "typeCode": "BP",
                "typeName": "BLOOD PRESSURE",
                "displayName": "Blood Pressure",
                "result": "120/80",
                "observed": "2024-01-15T10:30:00",
                "resulted": "2024-01-15T10:35:00",
                "facilityCode": "500",
                "facilityName": "Washington DC VAMC",
            }
        ],
        "lab_results": [
            {
                "uid": "urn:va:lab:500:100:1",
                "localId": "1",
                "typeCode": "GLUCOSE",
                "typeName": "GLUCOSE",
                "displayName": "Glucose",
                "result": "95",
                "numericResult": 95.0,
                "units": "mg/dL",
                "low": 70,
                "high": 110,
                "observed": "2024-01-15T08:00:00",
                "resulted": "2024-01-15T09:00:00",
                "interpretationCode": "N",
                "interpretationName": "NORMAL",
                "facilityCode": "500",
                "facilityName": "Washington DC VAMC",
            }
        ],
        "consults": [
            {
                "uid": "urn:va:consult:500:100:1",
                "localId": "1",
                "service": "CARDIOLOGY",
                "statusCode": "P",
                "statusName": "PENDING",
                "urgency": "R",
                "dateTime": "2024-01-15T14:00:00",
                "reason": "Chest pain evaluation",
                "providerName": "DOCTOR,TEST",
            }
        ],
    }


@pytest.fixture
def sample_rpc_response():
    """Sample RPC response for testing"""
    return {
        "data": {
            "totalItems": 1,
            "items": {
                "patient": {
                    "uid": "urn:va:patient:500:100",
                    "pid": "500;100",
                    "localId": "100",
                    "fullName": "TEST,PATIENT",
                    "familyName": "TEST",
                    "givenNames": ["PATIENT"],
                }
            },
        }
    }
