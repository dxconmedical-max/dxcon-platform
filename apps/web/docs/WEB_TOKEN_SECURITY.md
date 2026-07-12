# Web token and session security

## Actual strategy (honest)

DxCon web pilot authentication uses **Bearer JWT tokens** stored in the browser **`sessionStorage`** via Zustand persist (`dxcon-auth-v2`).

HttpOnly cookie authentication is **not** implemented end-to-end. Middleware uses short-lived **indicator cookies** (`dxcon_authenticated`, `dxcon_role`, `dxcon_organization_id`) for route gating only — these are not access tokens.

## Token storage

| Item | Location | Notes |
|------|----------|-------|
| Access token | `sessionStorage` | Cleared when tab session ends |
| Refresh token | `sessionStorage` | Used for `/api/v1/auth/refresh` and `/api/v1/auth/logout` |
| Auth indicator cookies | Document cookie | Set on login; cleared on logout |

Tokens are **never** placed in URLs or logged to the console.

## Session lifecycle

1. **Login** — `POST /api/v1/auth/login` returns access + refresh tokens
2. **Resolve context** — `GET /api/v1/auth/me`, `GET /api/v1/auth/capabilities`
3. **Restore** — On `/app` load, refresh expired access tokens via `POST /api/v1/auth/refresh`
4. **Logout** — `POST /api/v1/auth/logout` (refresh revocation) + local state/cache clear

## Organization context

Authenticated API calls include:

- `Authorization: Bearer <access_token>`
- `X-Organization-ID: <uuid>` when organization is selected

Organization switch clears tenant-scoped client caches via `clearTenantScopedCaches()`.

## Protected route behavior

- Unauthenticated → `/login`
- Expired session → `/login?reason=session-expired`
- Missing organization → `/select-organization`
- Forbidden → `/forbidden`

Application shell shows a loading spinner until auth hydration completes to avoid protected-content flash.

## Production requirements

- `NEXT_PUBLIC_DEMO_MODE=false` in production (demo account selector hidden)
- No mock authentication in production builds
- Backend remains authoritative for permissions and tenant isolation

## Future hardening (not in this sprint)

- HttpOnly cookie session with CSRF protection
- Refresh token rotation
- Short-lived access tokens with silent refresh only
