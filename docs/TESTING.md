# Testing Guide

Comprehensive testing guide with prompts, test data, and examples for the Vista API MCP Server.

## Quick Test Prompts

Use these prompts to quickly verify the MCP server is working correctly:

### Basic Verification
1. "Check if the Vista system is online"
2. "What's the current server time?"
3. "Show me the Vista server version"

### Patient Search
1. "Search for patients with last name ANDERSON"
2. "Find patients whose last name starts with MART"
3. "Look up patient THOMPSON,MICHAEL"
4. "Search for patient GARCIA"

### Clinical Data Retrieval
1. "Show me medications for patient 100022"
2. "Get lab results for patient 100023 from the last 30 days"
3. "Get vital signs for patient 100024"
4. "List active problems for patient 100025"

## Test Data Reference

### Test Patients

| Patient Name | DFN | Description | Key Conditions |
|-------------|-----|-------------|----------------|
| ANDERSON,JAMES ROBERT | 100022 | Vietnam Era Veteran | PTSD, Diabetes Type 2, Hypertension |
| MARTINEZ,MARIA ELENA | 100023 | Female Gulf War Veteran | Fibromyalgia, Depression, MST |
| THOMPSON,MICHAEL DAVID | 100024 | OEF/OIF Veteran | Polytrauma, TBI, Amputation |
| WILLIAMS,ROBERT EARL | 100025 | Elderly Korean War Veteran | Dementia, Former POW, Long-term care |
| JOHNSON,DAVID WAYNE | 100026 | Homeless Veteran | Substance abuse, Mental health |
| DAVIS,JENNIFER LYNN | 100027 | Recent Female Veteran | Transition assistance, Women's health |
| WILSON,GEORGE HENRY | 100028 | Rural Veteran | Telehealth, Travel eligible |
| GARCIA,ANTONIO JOSE | 100029 | Complex Medical Needs | Dialysis, Transplant candidate |

### Test Credentials

**Mock Server:**
- API Key: `test-wildcard-key-456`
- Station: `500`
- DUZ: `10000000219`

**Test Stations:**
- `500` - Washington DC VAMC (Primary)
- `442` - Ann Arbor VAMC (Secondary)
- `999` - Invalid station (for error testing)

## Comprehensive Test Scenarios

### Scenario 1: New Patient Intake
```
1. "Search for patient ANDERSON"
2. "Get demographics for patient 100022"
3. "Check allergies for patient 100022"
4. "Show medications for patient 100022"
5. "List active problems for patient 100022"
6. "Get vital signs for patient 100022"
```

### Scenario 2: Clinical Review
```
1. "Show medications for patient 100023"
2. "Get lab results for patient 100023 from the last 30 days"
3. "Check if patient 100023 has allergies"
4. "Get vital signs for patient 100023"
5. "Show active problems for patient 100023"
```

### Scenario 3: Appointment Management
```
1. "Show appointments for clinic 195"
2. "Get user profile for DUZ 10000000219"
3. "List team members"
4. "Show appointments for the next 7 days"
```

### Scenario 4: Error Handling
```
1. "Get data for patient 999999" (invalid patient)
2. "Search for patient X" (too short)
3. "Get medications for patient ABC" (invalid DFN)
```

## Expected Response Examples

### Patient Search Response
```json
{
  "success": true,
  "data": [
    {
      "id": "100022",
      "name": "ANDERSON,JAMES",
      "ssn": "***-**-1234",
      "dob": "03/15/1955",
      "age": 68,
      "gender": "M"
    }
  ],
  "message": "Found 1 patient(s)"
}
```

### Medications Response
```json
{
  "success": true,
  "data": {
    "medications": [
      {
        "name": "METFORMIN",
        "dosage": "1000MG",
        "schedule": "TWICE DAILY",
        "status": "ACTIVE",
        "prescriber": "DR. SMITH",
        "startDate": "01/15/2023"
      },
      {
        "name": "LISINOPRIL",
        "dosage": "10MG",
        "schedule": "DAILY",
        "status": "ACTIVE",
        "prescriber": "DR. JONES",
        "startDate": "06/20/2022"
      }
    ]
  }
}
```

### Lab Results Response
```json
{
  "success": true,
  "data": {
    "labs": [
      {
        "test": "HEMOGLOBIN A1C",
        "value": "7.2",
        "units": "%",
        "reference": "4.0-6.0",
        "flag": "H",
        "date": "10/15/2023"
      },
      {
        "test": "GLUCOSE",
        "value": "145",
        "units": "mg/dL",
        "reference": "70-110",
        "flag": "H",
        "date": "10/15/2023"
      }
    ]
  }
}
```

## Integration Testing

### Python Test Script
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
import sys

async def test_mcp_server():
    """Test basic MCP server functionality"""
    
    # Connect to server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"]
    )
    
    async with ClientSession(server_params) as session:
        # Initialize
        await session.initialize()
        
        # Test patient search
        result = await session.call_tool(
            "search_patients",
            arguments={"search_text": "Anderson"}
        )
        assert result.content[0].text.find("ANDERSON,JAMES") != -1
        
        # Test medications
        result = await session.call_tool(
            "get_medications",
            arguments={"patient_id": "100022"}
        )
        assert "METFORMIN" in result.content[0].text
        
        print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

### Bash Test Script
```bash
#!/bin/bash
# Quick MCP server test

echo "Testing Vista MCP Server..."

# Start server if not running
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "Starting mock server..."
    cd mock_server && docker-compose up -d
    sleep 5
fi

# Test with mcp-cli (if installed)
echo "1. Testing patient search..."
echo '{"tool": "search_patients", "arguments": {"search_text": "Anderson"}}' | mcp-cli

echo "2. Testing medications..."
echo '{"tool": "get_medications", "arguments": {"patient_id": "100022"}}' | mcp-cli

echo "Tests complete!"
```

## Performance Benchmarks

Expected response times for common operations:

| Operation | Expected Time | Max Time |
|-----------|--------------|----------|
| Patient Search | < 100ms | 500ms |
| Get Demographics | < 50ms | 200ms |
| Get Medications | < 150ms | 500ms |
| Get Lab Results | < 200ms | 1000ms |
| Get Full Patient Data | < 500ms | 2000ms |

## Common Issues and Solutions

### Issue: "Patient not found"
**Solution:** Verify you're using correct test patient DFNs (100022-100029)

### Issue: "Authentication failed"
**Solution:** Ensure mock server is running and using correct API key

### Issue: "Tool not found"
**Solution:** Check tool name spelling (use underscores, not hyphens)

### Issue: Slow responses
**Solution:** 
1. Check if mock server is running locally
2. Verify no network issues
3. Consider implementing caching

## Advanced Testing

### Load Testing with Locust
```python
from locust import HttpUser, task, between

class VistaMCPUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def search_patient(self):
        self.client.post("/tools/search_patients", json={
            "search_text": "Anderson"
        })
    
    @task
    def get_medications(self):
        self.client.post("/tools/get_medications", json={
            "patient_id": "100022"
        })
```

### Continuous Testing
Set up automated tests to run on every commit:

```yaml
# .github/workflows/test.yml
name: Test Vista MCP Server
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: |
          pip install -e .
          pytest tests/
```

## Debugging Tips

1. **Enable debug logging:**
   ```bash
   VISTA_MCP_DEBUG=true mise run dev-with-mock
   ```

2. **Check mock server logs:**
   ```bash
   docker-compose -f mock_server/docker-compose.yml logs -f
   ```

3. **Use MCP Inspector:**
   - Open http://localhost:6274
   - Enable request/response logging
   - Test individual tools interactively

4. **Verify mock data:**
   ```bash
   # Check if patient exists in mock
   curl http://localhost:8080/test/patients
   ```