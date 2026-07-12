# Report Verification

Public route: `/verify-report/[token]`  
API: `GET /api/v1/verify-report/{token}`

## Privacy

- Token is opaque (`secrets.token_urlsafe`)
- QR/payload contains **no PHI**
- Response: report code, version, status, amended/revoked flags only

## Operations

- Tokens expire per policy (default 365 days)
- Lookup events should be audited in production
- Rate limiting recommended at gateway layer
