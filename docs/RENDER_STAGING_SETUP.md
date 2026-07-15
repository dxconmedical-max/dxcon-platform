# Render Staging Setup — Release 9.0

Derived from `backend/render.yaml`, `backend/gunicorn.conf.py`, `backend/run.py`, `backend/Dockerfile`.

---

## Services to create (manual)

| Resource | Suggested name | Notes |
|---|---|---|
| PostgreSQL | `dxcon-staging-postgres` | Separate from `dxcon-postgres` |
| Redis | `dxcon-staging-redis` | Separate from production Redis |
| Web Service | `dxcon-api-staging` | From Blueprint fields below |
| Background worker | **Optional / not required for MVP staging** | `production_start.py worker` is a placeholder sleep loop |
| Scheduler / cron | **Optional / not required** | No Celery/RQ in Render Blueprint |

---

## Exact Web Service fields

| Field | Value (from repository) |
|---|---|
| Service name | `dxcon-api-staging` |
| Repository | Same GitHub repo as production |
| Branch | `release/8.1-production-integration` |
| Root Directory | `backend` |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn -c gunicorn.conf.py run:app` |
| Health Check Path | `/api/v1/system/health` |
| Auto-Deploy | Enable for staging branch only |
| Region | Match staging Postgres |

### Optional Docker start

```text
python production_start.py api
```

Health alternate (Docker HEALTHCHECK): `/live` — prefer `/api/v1/system/health` for Render to match Blueprint.

---

## Environment variables (names)

Set in Render UI — never commit values:

`APP_ENV`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`, `MARKETPLACE_PAYMENT_WEBHOOK_SECRET`, `DEMO_MODE=false`, `LOG_FORMAT=json`, `STARTUP_VALIDATE_DB=true`

`CORS_ORIGINS` exact staging value:

```text
https://staging.dxcon.com.vn,https://app-staging.dxcon.com.vn
```

---

## Migration command (run against staging DB only)

From repo root (after `DATABASE_URL` points at staging):

```bash
export DATABASE_URL="<STAGING_POSTGRESQL_URL>"
# Fresh staging: run 001–015 first (see PRODUCTION_MIGRATION_RUNBOOK)
for f in backend/migrations/01{6,7,8,9}_*.sql backend/migrations/020_*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

Full details: `docs/STAGING_MIGRATION_EXECUTION.md`.

---

## Worker / scheduler

| Process | Command in repo | Staging recommendation |
|---|---|---|
| Worker | `python production_start.py worker` | Optional; placeholder only |
| Scheduler | `python production_start.py scheduler` | Optional; placeholder only |

Do not claim background jobs are production-ready until real workers are configured.

---

## Custom domain

1. Render → `dxcon-api-staging` → Custom Domains → add `api-staging.dxcon.com.vn`  
2. Copy the **exact** CNAME/A target Render displays  
3. Create Cloudflare DNS **DNS only** (grey cloud)  
4. Wait for certificate → verify `https://api-staging.dxcon.com.vn/api/v1/system/health`
