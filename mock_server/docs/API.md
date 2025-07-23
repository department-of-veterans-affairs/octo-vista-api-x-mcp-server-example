# Vista API X Mock - API Reference

## Authentication

### Get Token
```
POST /auth/token
Content-Type: application/json

{
  "key": "test-wildcard-key-456"
}
```

Returns:
```json
{
  "path": "/auth/token",
  "data": {
    "token": "eyJhbGci..."
  }
}
```

Tokens expire after 1 hour. Use the token in the Authorization header:
```
Authorization: Bearer YOUR_TOKEN
```

## RPC Invocation

```
POST /vista-sites/{station}/users/{duz}/rpc/invoke
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "context": "string",        // RPC context (required)
  "rpc": "string",            // RPC name (required)
  "parameters": [],           // Array of parameters
  "jsonResult": false         // Set true for JSON responses
}
```

### Parameter Format
```json
{
  "parameters": [
    {"string": "value"},      // String parameter
    {"array": ["A", "B"]},    // Array parameter
    {"ref": "value"}          // Reference parameter
  ]
}
```

## Common RPCs

### Search Patients
```json
{
  "context": "OR CPRS GUI CHART",
  "rpc": "ORWPT LIST",
  "parameters": [
    {"string": "^DOE"}        // Search by last name
  ]
}
```

### Get Patient Data (JSON)
```json
{
  "context": "LHS RPC CONTEXT",
  "rpc": "VPR GET PATIENT DATA JSON",
  "jsonResult": true,
  "parameters": [
    {"string": "100022"},     // Patient DFN
    {"string": ""},           // Start date (optional)
    {"string": ""},           // End date (optional)
    {"string": "patient;vital;med;problem;allergy"}  // Domains
  ]
}
```

### Get Medications
```json
{
  "context": "OR CPRS GUI CHART",
  "rpc": "ORWPS ACTIVE",
  "parameters": [
    {"string": "100022"}      // Patient DFN
  ]
}
```

### Get Lab Results
```json
{
  "context": "OR CPRS GUI CHART",
  "rpc": "ORWLRR INTERIM",
  "parameters": [
    {"string": "100022"},     // Patient DFN
    {"string": "1"},          // Start date offset
    {"string": "10"}          // End date offset
  ]
}
```

### Get Vital Signs
```json
{
  "context": "OR CPRS GUI CHART",
  "rpc": "ORQQVI VITALS",
  "parameters": [
    {"string": "100022"}      // Patient DFN
  ]
}
```

## Test Data Reference

### Test Patients

| DFN | Name | Primary Conditions |
|-----|------|--------------------|
| 100022 | ANDERSON,JAMES | Vietnam vet, PTSD, diabetes |
| 100023 | SMITH,MARY | Gulf War vet, fibromyalgia |
| 100024 | JOHNSON,ROBERT | OEF/OIF vet, polytrauma |
| 100025 | WILLIAMS,PATRICIA | Elderly, dementia |
| 100026 | BROWN,MICHAEL | Homeless, substance use |
| 100027 | DAVIS,JENNIFER | Recent vet, women's health |
| 100028 | MILLER,LINDA | Rural, telehealth |
| 100029 | WILSON,THOMAS | Complex medical, dialysis |

### Test Providers

- **10000000219** - Primary test user (Dr. Susan Chen)
- **10000000220-224** - Other providers

### Test Stations

- **500** - Washington DC VAMC (primary)
- **508** - Atlanta VAMC
- **640** - Palo Alto VAMC

## Error Responses

Errors follow this format:
```json
{
  "success": false,
  "errorCode": "ERROR-CODE",
  "responseStatus": 401,
  "title": "Error Title",
  "message": "Detailed error message",
  "path": "/vista-sites/500/users/123/rpc/invoke"
}
```

Common error codes:
- `JWT-EXPIRED` - Token expired (401)
- `ACCESS-DENIED` - Not authorized (403)
- `RPC-NOT-FOUND` - Invalid RPC (404)
- `PARAMETER-ERROR` - Invalid parameters (400)

## Available RPCs

**Patient Operations:** ORWPT LIST, ORWPT ID INFO, ORWPT SELECT, VPR GET PATIENT DATA JSON

**Clinical:** ORWPS ACTIVE, ORWLRR INTERIM, ORQQVI VITALS, ORQQPL PROBLEM LIST, ORQQAL LIST

**Administrative:** SDES GET APPTS BY CLIN IEN 2, ORWTPD1 LISTALL

**System:** XWB IM HERE, ORWU DT, ORWU USERINFO, ORWU VERSRV

**Data Dictionary (requires wildcard key):** DDR LISTER, DDR FIND, DDR GETS

## Tips

1. Use `test-wildcard-key-456` for full access to all RPCs
2. Patient DFNs are 100022-100029 (8 patients total)
3. Add `"jsonResult": true` for JSON responses from RPCs that support it
4. Tokens expire after 1 hour - refresh or get new token as needed