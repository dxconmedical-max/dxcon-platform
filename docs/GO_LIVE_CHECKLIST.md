# DxCon Production Go-Live Checklist — v1.0.0-rc1

**Version:** `1.0.0-rc1`  
**Branch:** `tmp/cors-to-main`  
**Auth:** FROZEN (`docs/AUTH_FREEZE.md`) — do not change web auth runtime without freeze exception.  
**State:** Release Candidate prepared — see remaining P0/P1 in `docs/RC_AUDIT_REPORT.md` before declaring GA.

---

## Production URLs

| Surface | URL |
|---------|-----|
| Web app | https://dxcon.com.vn |
| API | https://api.dxcon.com.vn (Render: `dxcon-ap.onrender.com`) |
| Health | `GET /api/v1/system/health` |
| Live | `GET /api/v1/system/live` |
| Ready | `GET /api/v1/system/ready` |
| Report verify | `/results/verify/report/<code>` |

---

## Admin account

- Provision via gated `POST /api/v1/security/users` (ADMIN+) after deploy — **not** via public `/auth/register` (PATIENT-only).
- Rotate default/demo passwords before cutover.
- Store credentials in the org secret manager (never in git).

---

## Environment variables (minimum)

### Backend (Render)

| Key | Notes |
|-----|--------|
| `APP_ENV` | `production` |
| `SECRET_KEY` / `JWT_SECRET_KEY` | generated / rotated |
| `DATABASE_URL` | Postgres (from Render DB) |
| `REDIS_URL` | **required** for multi-instance / rate-limit / queue durability |
| `CORS_ORIGINS` | apex + role subdomains (see `backend/render.yaml`) |
| `DEMO_MODE` | `false` |
| `API_AUTH_GATE_ENABLED` | `true` |
| `SMTP_*` | required for mail |
| `BUILD_VERSION` | `1.0.0-rc1` |
| `LOG_FORMAT` | `json` |
| `STORAGE_BACKEND` / S3 | S3 for multi-node |

### Frontend (Vercel)

| Key | Notes |
|-----|--------|
| `NEXT_PUBLIC_APP_ENV` | `production` |
| `NEXT_PUBLIC_API_BASE_URL` | https://api.dxcon.com.vn |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` / `NEXT_PUBLIC_APP_URL` | https://dxcon.com.vn |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |

### Mobile (`apps/mobile`)

- Use `config/production.env.json` + `--dart-define-from-file`
- No secrets in source; Sentry DSN only via CI secrets when approved

---

## Deployment steps

1. Database backup (see Backup below).
2. Apply SQL migrations in order under `backend/migrations/` (note: `016_reporting_engine.sql` was renumbered from duplicate `007`).
3. Deploy backend (`backend/render.yaml` / `gunicorn -c gunicorn.conf.py run:app`).
4. Confirm `/api/v1/system/health`, `/live`, `/ready`.
5. Deploy web (Vercel) with production env validation (`apps/web/next.config.ts`).
6. Smoke: login → reception → collection → lab → PDF → role dashboards.
7. Confirm CORS from browser origins; confirm anonymous `/api/v1/patients` returns **401**.
8. Tag release `v1.0.0-rc1`.

---

## Rollback plan

1. Revert Render/Vercel deploy to previous successful build/commit.
2. Restore Postgres from pre-deploy backup if schema changed.
3. Invalidate CDN/cache if used.
4. Announce incident; capture correlation IDs from JSON logs.

---

## Database backup / restore

- See `docs/BACKUP.md`, `docs/BACKUP_RESTORE_RUNBOOK.md`, `docs/DISASTER_RECOVERY.md`.
- Pre-RC: take a full Postgres dump; store off-box.
- Restore: stop writers → restore dump → verify `/ready` → smoke critical paths.

---

## Monitoring / alerting

| Signal | Endpoint / source |
|--------|-------------------|
| Liveness | `/api/v1/system/live` |
| Readiness | `/api/v1/system/ready` |
| Health | `/api/v1/system/health` |
| Structured logs | `LOG_FORMAT=json` + correlation / request IDs |
| Metrics | Prometheus exporter — require auth in production |
| Mobile crash | Sentry DSN (optional; off if unset) |

Alert on: 5xx rate, ready=DEGRADED, DB errors, queue depth (when Redis queue enabled).

---

## Incident response

Follow `docs/INCIDENT_RESPONSE.md` / `docs/INCIDENT_RUNBOOK.md`.

Severity cheat-sheet:
- **SEV-1:** PHI leak, auth bypass, data loss
- **SEV-2:** Workflow blocked (orders/lab/PDF)
- **SEV-3:** Degraded UX / single-role outage

---

## Known issues (RC1)

See `docs/RC_AUDIT_REPORT.md` for full P0/P1/P2.

Summary:
- Manual SQL migrations (no Alembic runner yet)
- Worker/scheduler placeholders in compose
- Redis/SMTP must be provisioned on Render (not auto-wired)
- Auth freeze: JWT in client storage (XSS residual risk)
- Flutter Phase 1: local Android/iOS SDK builds may be incomplete; CI configured

---

## Release notes / version

- `docs/VERSION.md` → `1.0.0-rc1`
- `docs/CHANGELOG.md`
- `docs/RELEASE_NOTES.md`

---

## Sign-off

| Check | Owner | Done |
|-------|-------|------|
| P0 security gates deployed | Eng | [ ] |
| Migrations applied | Ops | [ ] |
| Backup verified | Ops | [ ] |
| E2E smoke on production Postgres | QA | [ ] |
| Auth freeze regression | Eng | [ ] |
| Go / No-Go decision | Release Manager | [ ] |
