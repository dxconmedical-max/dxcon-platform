# DxCon Auth API Contract

Production API base: `https://api.dxcon.com.vn`

## Authentication

### POST `/api/v1/auth/login`

**Request**
```json
{ "email": "user@example.com", "password": "..." }
```

**Response 200**
```json
{
  "success": true,
  "token": "<access_jwt>",
  "access_token": "<access_jwt>",
  "refresh_token": "<refresh_jwt>",
  "email": "user@example.com",
  "role": "DOCTOR",
  "user": { "id", "email", "phone", "role", "organization_id", "is_active", "created_at", "updated_at" }
}
```

**Errors:** `401` invalid credentials, `403` account disabled

### POST `/api/v1/auth/refresh`

**Auth:** Bearer refresh token

**Response 200**
```json
{ "success": true, "token": "<access_jwt>", "access_token": "<access_jwt>", "refresh_token_claims": { "type", "exp" } }
```

### POST `/api/v1/auth/logout`

**Auth:** Bearer refresh token

**Response 200:** `{ "success": true, "message": "Logged out" }`

### GET `/api/v1/auth/me` *(Epic 2)*

**Auth:** Bearer access token

**Response 200**
```json
{
  "success": true,
  "data": {
    "user": { ... },
    "active_organization_id": "...",
    "memberships": [ ... ],
    "requires_organization_selection": false
  }
}
```

### GET `/api/v1/auth/memberships` *(Epic 2)*

**Auth:** Bearer access token

Returns active memberships with organization metadata and `membership_status`.

### POST `/api/v1/auth/switch-organization` *(Epic 2)*

**Auth:** Bearer access token

**Request:** `{ "organization_id": "<uuid>" }`

**Response 200:** capabilities payload (permissions, features, workspace)

**Errors:** `403` disabled membership, suspended organization

### GET `/api/v1/auth/capabilities` *(Epic 2)*

**Auth:** Bearer access token

**Query:** `organization_id` (optional)

**Response 200**
```json
{
  "success": true,
  "data": {
    "user": { ... },
    "organization": { ... },
    "membership": { "membership_id", "organization_id", "role_code", "membership_status" },
    "workspace": "/app/doctor",
    "permissions": ["..."],
    "features": ["HOME_COLLECTION", "MARKETPLACE"]
  }
}
```

### POST `/api/v1/auth/forgot-password` *(Epic 2)*

**Request:** `{ "email": "..." }`

**Response 200:** generic success message (no email enumeration)

### POST `/api/v1/auth/reset-password` *(Epic 2)*

**Status:** `501` — self-service reset not yet enabled

## Partner foundation (admin)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/partner/organizations` | List organizations |
| GET | `/api/v1/partner/users` | List memberships |
| GET | `/api/v1/partner/permissions` | Org role permission matrix |

## Workspace routing

Role selects **default workspace path** only. Access is enforced by permissions + membership, not role alone.

See `src/lib/roles.ts` and backend `app/web_gateway/routing.py`.

## Gaps documented in `generated-release/AUTH_BACKEND_GAPS.json`

- Password reset token delivery not implemented
- JWT does not embed `organization_id` (resolved via `/me` + headers)
- HttpOnly cookie auth not end-to-end (bearer tokens required)
