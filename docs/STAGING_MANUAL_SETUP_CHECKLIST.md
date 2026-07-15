# Staging Manual Setup Checklist — Release 9.0

**Source branch:** `release/8.1-production-integration`  
**Stop:** after each section, copy values from the provider UI (do not invent DNS targets).

---

## 1. Render — Staging PostgreSQL

| Field | Value / copy from UI | Done |
|---|---|---|
| Provider | Render → New → PostgreSQL | ☐ |
| Name | `dxcon-staging-postgres` | ☐ |
| Database | `dxcon_staging` | ☐ |
| Region | Same region as staging API | ☐ |
| Internal Database URL | → paste into `DATABASE_URL` | ☐ |
| **Confirm not production DB** | Separate instance from `dxcon-postgres` | ☐ |

## 2. Render — Staging Redis

| Field | Value / copy from UI | Done |
|---|---|---|
| Provider | Render → New → Redis (or Key Value) | ☐ |
| Name | `dxcon-staging-redis` | ☐ |
| Redis URL | → paste into `REDIS_URL` | ☐ |
| **Confirm not production Redis** | Separate instance | ☐ |

## 3. Render — Staging Web Service

| Field | Exact repository value | Done |
|---|---|---|
| Name | `dxcon-api-staging` | ☐ |
| Repository | `dxconmedical-max/dxcon-platform` | ☐ |
| Branch | `release/8.1-production-integration` | ☐ |
| Root Directory | `backend` | ☐ |
| Runtime | Python | ☐ |
| Build Command | `pip install -r requirements.txt` | ☐ |
| Start Command | `gunicorn -c gunicorn.conf.py run:app` | ☐ |
| Health Check Path | `/api/v1/system/health` | ☐ |
| Auto-Deploy | On for this branch only | ☐ |

Environment variables: see `docs/STAGING_ENVIRONMENT_CONTRACT.md` (names only; paste secrets in Render UI).

## 4. Migrations (staging DB only)

Follow `docs/STAGING_MIGRATION_EXECUTION.md`.

| Step | Done |
|---|---|
| Backup/snapshot staging DB | ☐ |
| Apply 001–015 if fresh, then 016–020 | ☐ |
| Run post-check SQL | ☐ |
| Backend health 200 | ☐ |

## 5. Pilot accounts

Follow `docs/STAGING_PILOT_ACCOUNTS.md` + `backend/scripts/bootstrap_staging_pilot.py`.

| Step | Done |
|---|---|
| Export `STAGING_*` emails/passwords from password manager | ☐ |
| Dry-run bootstrap | ☐ |
| Apply bootstrap | ☐ |
| Login smoke for each role | ☐ |

## 6. Vercel — Staging frontend

| Field | Exact value | Done |
|---|---|---|
| Project | Separate staging project **or** Preview for this branch | ☐ |
| Root Directory | `apps/web` | ☐ |
| Branch | `release/8.1-production-integration` | ☐ |
| Framework | Next.js | ☐ |
| Build Command | `npm run build` | ☐ |
| Install Command | `npm ci` | ☐ |
| Env vars | See environment contract | ☐ |

## 7. Domains + DNS

| Domain | Provider UI | Cloudflare (DNS only) | Done |
|---|---|---|---|
| `staging.dxcon.com.vn` | Vercel Domains → copy target | ☐ | ☐ |
| `app-staging.dxcon.com.vn` | Vercel Domains → copy target | ☐ | ☐ |
| `api-staging.dxcon.com.vn` | Render Custom Domains → copy target | ☐ | ☐ |

Do **not** change `dxcon.com.vn`, `www.dxcon.com.vn`, or `api.dxcon.com.vn`.

## 8. Smoke + UAT

| Step | Done |
|---|---|
| `node apps/web/scripts/staging-smoke-test.mjs` | ☐ |
| `python backend/scripts/staging_api_smoke_test.py` | ☐ |
| Execute `docs/STAGING_UAT_RELEASE_9.md` | ☐ |

---

## Next single action

Create **Render staging PostgreSQL** (`dxcon-staging-postgres`), then continue checklist §1–3.
