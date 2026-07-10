# Identity and Authentication Freeze — Release 2.0

## Frozen components

| Component | Location | Contract |
|-----------|----------|----------|
| User identity | `app/models/user.py` | email, role, organization_id, password_hash |
| Organization membership | `auth_context_service.py` | multi-org users, active org |
| JWT access token | `app/core/jwt_auth.py` | Bearer auth, claims |
| Login | `POST /api/v1/auth/login` | email + password → tokens |
| Refresh | `POST /api/v1/auth/refresh` | refresh token → new access |
| Logout | `POST /api/v1/auth/logout` | token invalidation |
| Me | `GET /api/v1/auth/me` | user + active org |
| Memberships | `GET /api/v1/auth/memberships` | org list |
| Switch org | `POST /api/v1/auth/switch-organization` | updates active context |
| Capabilities | `GET /api/v1/auth/capabilities` | permissions + features |

## Token claims (access)

- `sub` — user id
- `email`
- `role`
- `organization_id` — active organization
- `exp`, `iat`

## Session behavior

- Access token expiry: configured via app config (short-lived).
- Refresh token: longer-lived, rotation on refresh.
- Frontend (`apps/web`): tokens in `sessionStorage`, cleared on logout/session-expired.

## Known limitations (documented honestly)

1. **Password reset** — `POST /api/v1/auth/reset-password` returns 501 until SMTP is production-configured.
2. **Client-side token storage** — web app uses sessionStorage; XSS hygiene required.
3. **MFA** — not yet enforced platform-wide.
4. **OAuth/OIDC for patients** — foundation only; primary login is email/password.

## Verification

`IDENTITY_AUTH_FREEZE_REPORT.json`
