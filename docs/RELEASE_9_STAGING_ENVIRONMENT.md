# Release 9.0 — Staging Environment

**Rule:** Staging must never use production Postgres, Redis, SMTP passwords, payment secrets, or real PHI.

---

## Recommended domains

| Role | Domain |
|---|---|
| Public | `staging.dxcon.com.vn` |
| Application | `app-staging.dxcon.com.vn` |
| API | `api-staging.dxcon.com.vn` |

DNS targets: copy **exact** values from Vercel Domains and Render Custom Domains after those resources are created. Do not invent targets.

---

## Backend (Render staging service)

```text
APP_ENV=staging
DATABASE_URL=<staging PostgreSQL URL>
REDIS_URL=<staging Redis URL>
SECRET_KEY=<staging-only strong secret>
JWT_SECRET_KEY=<staging-only different strong secret>
CORS_ORIGINS=https://staging.dxcon.com.vn,https://app-staging.dxcon.com.vn
SMTP_HOST=<mail-capture provider host>
SMTP_PORT=587
SMTP_USER=<staging smtp user>
SMTP_PASSWORD=<staging smtp password>
SMTP_FROM=noreply@staging.dxcon.local
SMTP_USE_TLS=true
DEMO_MODE=false
LOG_FORMAT=json
IOT_SIMULATOR_ENABLED=true
```

Payment: staging may use non-production adapters only. Never point staging webhook secrets at production gateways.

---

## Frontend (Vercel staging / preview project)

```text
NEXT_PUBLIC_API_BASE_URL=https://api-staging.dxcon.com.vn
NEXT_PUBLIC_PUBLIC_SITE_URL=https://staging.dxcon.com.vn
NEXT_PUBLIC_APP_URL=https://app-staging.dxcon.com.vn
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_DEMO_MODE=false
```

Root Directory: `apps/web`

---

## Manual resource checklist

| Resource | Provider UI value to copy | Done? |
|---|---|---|
| Staging Postgres | Internal connection string → `DATABASE_URL` | ☐ |
| Staging Redis | Redis URL → `REDIS_URL` | ☐ |
| Staging Render service URL | `__________` | ☐ |
| Staging Vercel project | `__________` | ☐ |
| `staging.dxcon.com.vn` DNS target from Vercel | `__________` | ☐ |
| `app-staging.dxcon.com.vn` DNS target from Vercel | `__________` | ☐ |
| `api-staging.dxcon.com.vn` DNS target from Render | `__________` | ☐ |

---

## Staging banner

Ensure operators can distinguish staging from production (UI label, env, or deployment banner). Synthetic pilot accounts only — see UAT package.
