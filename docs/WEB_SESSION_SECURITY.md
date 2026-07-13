# DxCon Web Session Security

**Release:** 8.1 · **Sprint:** 9

---

## Cookie policy

| Cookie | Purpose | Set by | HttpOnly | Secure (prod) |
| --- | --- | --- | --- | --- |
| `dxcon_authenticated` | Edge middleware auth gate (`1` = authed) | Frontend after login | No (JS-readable for client guard) | Should be `Secure` in prod |
| `dxcon_role` | Middleware default-workspace redirect hint | Frontend after login | No | Should be `Secure` in prod |
| `dxcon_organization_id` | Active org context | Frontend after login/org switch | No | Should be `Secure` in prod |

> **Note:** JWT access/refresh tokens are held in client memory (not cookies) to reduce CSRF surface. The auth cookie is a lightweight gate for edge middleware only.

---

## Token lifecycle

1. **Login:** `POST /api/v1/auth/login` → access + refresh tokens returned in response body.
2. **API calls:** `Authorization: Bearer <access_token>` + `X-Organization-ID` on every request (`apps/web/src/lib/api/client.ts`).
3. **Refresh:** On 401, client attempts `POST /api/v1/auth/refresh` once; on failure, session cleared.
4. **Logout:** `POST /api/v1/auth/logout` (refresh token blocklisted) + all cookies cleared + in-memory tokens cleared + tenant caches cleared.

---

## Protected route guards (defense in depth)

| Layer | Mechanism | File |
| --- | --- | --- |
| Edge | Cookie `dxcon_authenticated=1` check; redirect to login | `apps/web/src/middleware.ts` |
| Client | `useRequireAuth()` → `restoreSession()` → permission check | `apps/web/src/hooks/useAuth.ts` |
| API | JWT validation + org membership + permission check | `backend/app/api/auth/` + route decorators |

Protected routes **must not** display clinical data before auth resolution completes. `AppShell` renders a spinner during hydration and `null` when unauthenticated.

---

## Cache control

`apps/web/next.config.ts` sets on `/app/:path*`:

```
Cache-Control: private, no-store, max-age=0
```

Protected workspace pages are never publicly cached.

---

## Security headers (frontend)

Applied to all routes via `next.config.ts`:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `X-Frame-Options: DENY`
- CSP `connect-src` includes production API origin only

---

## Logout and back-button protection

1. Logout calls backend revocation endpoint.
2. All cookies deleted.
3. In-memory token store cleared.
4. React Query / SWR caches cleared (if present).
5. User redirected to `/login`.
6. Protected routes re-check auth on navigation (middleware + client guard).

Back-button to a protected page after logout → middleware sees no auth cookie → redirect to login.

---

## Cross-tenant isolation

- Organization ID sent on every API request via `X-Organization-ID`.
- Backend enforces tenant scoping on all data queries.
- Frontend org switcher calls `POST /switch-organization` then reloads capabilities.
- Switching org clears workspace-specific cached data.

---

## Production prohibitions (enforced)

| Prohibition | Enforcement |
| --- | --- |
| Demo mode | Build fails if `NEXT_PUBLIC_DEMO_MODE=true` |
| Mock login | No mock auth code in frontend |
| Hardcoded credentials | None in source |
| PHI in URLs | No patient identifiers in query strings on public routes |
