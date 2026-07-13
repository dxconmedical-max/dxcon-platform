# DxCon Production Authentication Contract

**Release:** 8.1 · **Sprint:** 9
**Verified from:** `backend/app/api/auth/routes.py`, `apps/web/src/lib/api/auth.ts`

---

## Session / token strategy

| Aspect | Implementation |
| --- | --- |
| Access token | JWT, short-lived (`JWT_ACCESS_TOKEN_EXPIRES_HOURS`, default 1h) |
| Refresh token | JWT, long-lived (`JWT_REFRESH_TOKEN_EXPIRES_DAYS`, default 30d) |
| Token blocklist | Enabled (`JWT_BLOCKLIST_ENABLED=true`) |
| Frontend storage | Access + refresh tokens in memory/session; auth cookie `dxcon_authenticated=1` for edge middleware |
| Organization context | `X-Organization-ID` header on API calls; `dxcon_organization_id` cookie |
| Role hint | `dxcon_role` cookie (middleware redirect only; **permissions are authoritative**) |

---

## Backend endpoints (prefix `/api/v1/auth`)

| Method | Path | Auth required | Purpose |
| --- | --- | --- | --- |
| `POST` | `/login` | No | Email + password → access + refresh tokens |
| `POST` | `/refresh` | Refresh JWT | Rotate access token |
| `POST` | `/logout` | Refresh JWT | Revoke refresh token (blocklist) |
| `GET` | `/me` | Access JWT | Current user profile |
| `GET` | `/memberships` | Access JWT | User's organization memberships |
| `POST` | `/switch-organization` | Access JWT | Switch active organization |
| `GET` | `/capabilities` | Access JWT | Permissions + features for active org (`?organization_id=` optional) |
| `POST` | `/forgot-password` | No | Request password reset email (generic success always returned) |
| `POST` | `/reset-password` | No | **501 `RESET_NOT_ENABLED`** — not implemented |
| `POST` | `/register` | No | Self-registration (if enabled) |

There is **no separate feature-flags endpoint**. Features are returned in `/capabilities`.

---

## Frontend auth service mapping

File: `apps/web/src/lib/api/auth.ts`

| Frontend function | Backend call |
| --- | --- |
| `login(email, password)` | `POST /api/v1/auth/login` |
| `refreshSession()` | `POST /api/v1/auth/refresh` |
| `logout()` | `POST /api/v1/auth/logout` |
| `getCurrentUser()` | `GET /api/v1/auth/me` |
| `getMemberships()` | `GET /api/v1/auth/memberships` |
| `switchOrganization(id)` | `POST /api/v1/auth/switch-organization` |
| `getCapabilities(orgId?)` | `GET /api/v1/auth/capabilities` |
| `forgotPassword(email)` | `POST /api/v1/auth/forgot-password` |
| `resetPassword(token, password)` | `POST /api/v1/auth/reset-password` |

**No mock login. No hardcoded users. No fake role selection.**

---

## Login flow

1. User opens `https://app.dxcon.com.vn/login` (or redirected from protected route with `?next=`).
2. `POST /api/v1/auth/login` with email + password.
3. On success: tokens stored, cookies set (`dxcon_authenticated`, `dxcon_role`, `dxcon_organization_id`).
4. If single membership → redirect to role default workspace via `safeRedirectPath(next, workspacePathForRole(role))`.
5. If multiple memberships → redirect to `/select-organization`.
6. `useRequireAuth` calls `restoreSession()` → `GET /me` + `GET /capabilities` on each protected page load.

---

## Error handling

| Condition | Frontend behavior |
| --- | --- |
| Invalid credentials | Login form error message |
| Expired access token | Auto-refresh via `POST /refresh`; on failure → `/login?reason=session-expired` |
| Disabled user | Error from `/me`; redirect to login |
| Suspended membership | Error from `/capabilities`; redirect to `/forbidden` |
| Missing organization | Redirect to `/select-organization` |
| Insufficient permission | Redirect to `/forbidden` |
| Backend unavailable | `/service-unavailable` page |

---

## Safe redirect rules

`apps/web/src/lib/urls.ts` `safeRedirectPath()`:

- Rejects absolute URLs and protocol-relative paths in `?next=`
- Falls back to role default workspace or `/app`
- No open redirects

---

## Known limitations

| Item | Status |
| --- | --- |
| Password reset | Backend returns 501; reset page exists but flow is disabled |
| Demo mode | Blocked in production build (`NEXT_PUBLIC_DEMO_MODE=false` required) |
