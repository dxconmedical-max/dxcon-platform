# Staging Environment Contract — Release 9.0

**No secrets in Git.** Values below are names and allowed patterns only.

---

## Domains

| Role | URL |
|---|---|
| Public site | `https://staging.dxcon.com.vn` |
| Application | `https://app-staging.dxcon.com.vn` |
| API | `https://api-staging.dxcon.com.vn` |

---

## Frontend (`NEXT_PUBLIC_*`)

| Variable | Required value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | `https://staging.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_URL` | `https://app-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_ENV` | `staging` |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |

### Validation (code)

`apps/web/src/lib/env.ts` + `next.config.ts` for `staging`:

- Required vars must be present
- Localhost URLs rejected
- `DEMO_MODE=true` rejected

---

## Backend

| Variable | Required | Notes |
|---|---|---|
| `APP_ENV` | `staging` | Strict env; SQLite blocked |
| `DATABASE_URL` | Staging Postgres only | Never production |
| `REDIS_URL` | Staging Redis only | Never production |
| `SECRET_KEY` | Strong unique secret | Not production value |
| `JWT_SECRET_KEY` | Different strong secret | Not production value |
| `CORS_ORIGINS` | `https://staging.dxcon.com.vn,https://app-staging.dxcon.com.vn` | No production origins |
| `SMTP_HOST` | Staging/mail-capture host | Not production SMTP |
| `SMTP_PORT` | e.g. `587` | |
| `SMTP_USER` | Staging user | |
| `SMTP_PASSWORD` | Staging password | Secret in Render only |
| `SMTP_FROM` | `noreply@dxcon.com.vn` or staging-local | Honest wording if mail capture |
| `SMTP_USE_TLS` | `true` | |
| `MARKETPLACE_PAYMENT_WEBHOOK_SECRET` | Staging-only | Not production gateway secret |
| `DEMO_MODE` | `false` | |
| `LOG_FORMAT` | `json` | Required in staging |

### Simulator / payment policy

| Flag / adapter | Staging | Production |
|---|---|---|
| `DEMO_MODE` | Must be `false` | Must be `false` |
| `IOT_SIMULATOR_ENABLED` | Allowed only with explicit flag | Blocked unless force flags (see code) |
| `MOCK_TEST` payment adapter | **Blocked** in staging (`_STRICT_ENVS`) | Blocked |
| `MANUAL_BANK_QR` | Allowed; must display as manual/test | Allowed if configured |
| Live VNPay/MoMo claim | Forbidden unless verified live gateway | Forbidden unless verified |

---

## Isolation rules

1. No production Postgres / Redis / SMTP / payment secrets  
2. No real patient data  
3. UI shows **STAGING** banner (`IS_STAGING`)  
4. Password reset must not claim delivery without working SMTP  
5. Staging CORS must not include production apex/app origins  
