# Token Security — DxCon Web

## Current strategy (Epic 2)

The production API issues **JWT bearer tokens** (`access_token` + `refresh_token`) from `POST /api/v1/auth/login`.

### Storage

| Token | Storage | Rationale |
|-------|---------|-----------|
| Access token | `sessionStorage` (Zustand persist) | Short-lived; cleared on tab close |
| Refresh token | `sessionStorage` | Required for `/auth/refresh` and `/auth/logout` |
| Session hint cookie | `dxcon_authenticated` (non-HttpOnly) | Middleware route guard only — **not a secret** |

### What we do NOT do

- Tokens are **never** placed in URLs or query strings
- Passwords, tokens, and clinical data are **not** logged to console
- We do **not** claim HttpOnly cookie authentication — the backend does not set HttpOnly session cookies for the Next.js app today

### Logout

1. `POST /api/v1/auth/logout` with refresh token (best effort)
2. Clear Zustand auth state
3. Clear session storage
4. Clear session hint cookies

### Session expiry

- Access token expiry checked client-side via JWT `exp`
- On expiry: attempt refresh; on failure redirect to `/login?reason=session-expired`
- API `401` responses trigger the same flow

### Organization context

Active organization is sent via `X-Organization-ID` header on API requests after selection.

### Future improvement

When the backend supports HttpOnly cookie sessions for SPA clients, migrate access/refresh tokens out of `sessionStorage` and use cookie-based auth with CSRF protection.
