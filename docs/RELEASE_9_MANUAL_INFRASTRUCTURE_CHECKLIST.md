# Release 9.0 — Manual Infrastructure Checklist

**Source branch:** `release/8.1-production-integration`  
**Do not commit secret values into the repository.**  
**Fill actual values only in Render / Vercel / Cloudflare dashboards and a secure vault.**

---

## Status legend

| Field | Meaning |
|---|---|
| `__________` | Operator must paste the live value from the provider UI |
| PASS/FAIL | Fill after verification |

---

## 1. RENDER BACKEND (production service)

**Service name:** `__________`  
**Service URL / Render hostname:** `__________`  
**Git branch to deploy:** `release/8.1-production-integration`  
**Health check path:** `/api/v1/system/health`

### Environment variables (copy exact keys)

| Variable | Value template | Set? | Verified? |
|---|---|---|---|
| `APP_ENV` | `production` | ☐ | ☐ |
| `DATABASE_URL` | `<production PostgreSQL URL>` | ☐ | ☐ |
| `REDIS_URL` | `<production Redis URL>` | ☐ | ☐ |
| `SECRET_KEY` | `<strong secret, min 32 chars, unique>` | ☐ | ☐ |
| `JWT_SECRET_KEY` | `<different strong secret, min 32 chars>` | ☐ | ☐ |
| `CORS_ORIGINS` | `https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn` | ☐ | ☐ |
| `SMTP_HOST` | `<provider host>` | ☐ | ☐ |
| `SMTP_PORT` | `<provider port>` (typically `587`) | ☐ | ☐ |
| `SMTP_USER` | `<provider user>` | ☐ | ☐ |
| `SMTP_PASSWORD` | `<provider password>` | ☐ | ☐ |
| `SMTP_FROM` | `<approved sender>` | ☐ | ☐ |
| `SMTP_USE_TLS` | `true` | ☐ | ☐ |
| `MARKETPLACE_PAYMENT_WEBHOOK_SECRET` | `<strong secret>` | ☐ | ☐ |
| `DEMO_MODE` | `false` | ☐ | ☐ |
| `LOG_FORMAT` | `json` | ☐ | ☐ |

### Render verification

| Check | Expected | PASS/FAIL | Evidence |
|---|---|---|---|
| Service boots | No startup RuntimeError | | |
| Health | `GET /api/v1/system/health` → 200 | | |
| CORS allowlist | Live ACAO for `app.dxcon.com.vn` | | |
| Redis | Connectivity OK in readiness | | |

**Exact production CORS_ORIGINS (must match exactly):**

```text
CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
```

Do **not** include staging origins. Do **not** use `*`.

---

## 2. VERCEL PRODUCTION (frontend)

**Project name:** `__________`  
**Root Directory:** `apps/web`  
**Framework:** Next.js  
**Git branch:** `release/8.1-production-integration`

### Environment variables (Production scope)

| Variable | Required value | Set? | Verified? |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api.dxcon.com.vn` | ☐ | ☐ |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | `https://dxcon.com.vn` | ☐ | ☐ |
| `NEXT_PUBLIC_APP_URL` | `https://app.dxcon.com.vn` | ☐ | ☐ |
| `NEXT_PUBLIC_APP_ENV` | `production` | ☐ | ☐ |
| `NEXT_PUBLIC_DEMO_MODE` | `false` | ☐ | ☐ |

### Domains

| Domain | Purpose | Added in Vercel? | DNS target from Vercel | Cloudflare proxy | PASS/FAIL |
|---|---|---|---|---|---|
| `dxcon.com.vn` | Public site | ☐ | `__________` | DNS only initially | |
| `www.dxcon.com.vn` | Redirect to apex | ☐ | `__________` | DNS only initially | |
| `app.dxcon.com.vn` | Auth + workspaces | ☐ | `__________` | DNS only until SSL valid | |

> Copy the DNS target **exactly as shown by Vercel** after adding the domain. Do not invent hostnames or IPs.

---

## 3. CLOUDFLARE DNS

| Record | Type | Name | Target (from provider) | Proxy mode | PASS/FAIL |
|---|---|---|---|---|---|
| Apex (if needed) | A/CNAME | `@` / `dxcon.com.vn` | `__________` | DNS only until verified | |
| www | CNAME | `www` | `__________` | DNS only until verified | |
| app | CNAME | `app` | `__________` | DNS only until cert issued | |
| api | CNAME | `api` | `__________` (Render custom domain target) | DNS only recommended | |

---

## 4. STAGING (separate from production)

Create identical structure with **isolated** Postgres, Redis, backend, and frontend.

| Variable | Staging template |
|---|---|
| `APP_ENV` | `staging` |
| `CORS_ORIGINS` | `https://staging.dxcon.com.vn,https://app-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_API_BASE_URL` | `https://api-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | `https://staging.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_URL` | `https://app-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_ENV` | `staging` |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |

See `docs/RELEASE_9_STAGING_ENVIRONMENT.md`.

---

## 5. Operator sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Backend owner | | | |
| Frontend owner | | | |
| Security reviewer | | | |

**Next single action after this checklist is opened:** set production Render `CORS_ORIGINS` to the exact three origins above and redeploy the backend service.
