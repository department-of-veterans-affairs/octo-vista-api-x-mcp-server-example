# JWT Structure Comparison: Dev Environment vs Mock Server

## Key Differences

### 1. Top-Level Structure
**Dev Environment JWT** has fields directly at the root level:
- `authenticated`, `lastName`, `firstName`, `email` at root
- `vistaIds` at root level
- Uses `vamf.auth.resources` and `vamf.auth.roles`
- Has `authenticationAuthority`, `version`, `userType`, `loa`

**Mock Server JWT** nests user data:
- User fields are inside a `user` object
- `authorities` inside the `user` object
- No `vamf.auth.resources`
- Different issuer (`gov.va.vista.api` vs `gov.va.vamf.userservice.v2`)

### 2. Authorization Structure

**Dev Environment**:
```json
{
  "vamf.auth.resources": [
    "^.*(/)?patient[s]?(/.*)?$",
    "^.*(/)?staff/1014354511(/.*)?$",
    "^.*(/)?site[s]?/(dfn-)?(500|530)(/.*)?$"
  ],
  "vamf.auth.roles": ["staff", "va", "hcp"]
}
```

**Mock Server**:
```json
{
  "user": {
    "authorities": [
      {"context": "OR CPRS GUI CHART", "rpc": "*"},
      {"context": "LHS RPC CONTEXT", "rpc": "*"}
    ]
  }
}
```

### 3. Vista IDs Structure

**Dev Environment**:
```json
{
  "vistaIds": [
    {
      "siteId": "530",
      "siteName": "Site #530",
      "duz": "520824792"
    }
  ]
}
```

**Mock Server**:
```json
{
  "user": {
    "vistaIds": [
      {
        "siteId": "500",
        "duz": "10000000219",
        "siteName": ""
      }
    ]
  }
}
```

### 4. Missing Fields in Mock Server

The mock server JWT is missing:
- `authenticationAuthority`
- `version`
- `userType`
- `loa` (Level of Assurance)
- `sst` (Session Start Time)
- `staffDisclaimerAccepted`
- `vamf.auth.resources`
- Direct root-level user fields

### 5. Authorization Model Difference

The dev environment uses:
- **Resource-based authorization** with regex patterns for patient/staff/site access
- **Role-based authorization** with roles like "staff", "va", "hcp"

The mock server uses:
- **RPC-based authorization** with context/RPC pairs
- No resource patterns or roles

## Recommendation

The mock server's JWT structure appears to follow an older Vista API X pattern focused on RPC authorization, while the dev environment uses a newer VAMF (VA Mobile Framework) pattern with resource-based authorization.

For compatibility, the mock server should be updated to:
1. Move user fields to root level
2. Add `vamf.auth.resources` with appropriate patterns
3. Add `vamf.auth.roles`
4. Update the issuer to match production
5. Add missing fields like `version`, `loa`, etc.