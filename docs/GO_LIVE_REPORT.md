# DxCon Go-Live Report — v1.0.0

**Generated:** 2026-07-24  
**Repo HEAD verified:** `c3183a50efb1fa60effa83765e15af87c436df7e` (`tmp/cors-to-main`)  
**Live API build observed:** `version=2.5.0-dev`, `environment=staging`, `git_sha=local`  
**Verdict:** **NOT READY FOR PRODUCTION** — open P0 blockers remain.

Auth freeze: unchanged (web auth runtime not modified).

---

## Summary

| Result | Count |
|--------|------:|
| PASS | 11 |
| WARNING | 6 |
| FAIL (P0) | 8 |

**Do not declare `DxCon v1.0.0 READY FOR PRODUCTION` until every FAIL below is closed and re-verified on the live stack.**

---

## Checklist results

### 1. Production URLs

| Item | Status | Evidence |
|------|--------|----------|
| https://dxcon.com.vn | **PASS** | HTTP 200, Next.js HTML |
| https://www.dxcon.com.vn | **PASS** | HTTP 200 |
| https://app.dxcon.com.vn | **FAIL** | DNS NXDOMAIN (`Could not resolve host`) |
| https://api.dxcon.com.vn | **WARNING** | Live/version OK; health intermittent timeout once; ready 503 |
| Role app paths (`/app/admin|patient|reception|lab|collector`) | **PASS** | 307 → login (middleware present) via Vercel |
| `/login` | **PASS** | HTTP 200 |

### 2. Render deployment

| Item | Status | Evidence |
|------|--------|----------|
| Service reachable (`dxcon-ap.onrender.com`) | **PASS** | `/live` 200, `/health` 200 |
| Deployed revision matches RC (`c3183a5` / `1.0.0-rc*`) | **FAIL** | Live reports `2.5.0-dev` / `git_sha=local` / `APP_ENV=staging` — RC security + version not on live |
| Health check path | **WARNING** | Render uses `/api/v1/system/health` (OK) but `/ready` returns 503 |

### 3. Vercel deployment

| Item | Status | Evidence |
|------|--------|----------|
| Apex served by Vercel | **PASS** | `server: Vercel`, `x-vercel-cache: HIT`, HSTS present |
| CSP + security headers | **WARNING** | CSP includes `'unsafe-inline'` / `'unsafe-eval'` (known RC risk) |

### 4. Environment variables

| Item | Status | Evidence |
|------|--------|----------|
| Secrets present (JWT/SECRET from env) | **PASS** | health `jwt_secret_from_env` / `secret_key_from_env` true |
| `APP_ENV=production` | **FAIL** | Live `app_env` / build environment = **`staging`** |
| `BUILD_VERSION=1.0.0` / RC | **FAIL** | Live `version=2.5.0-dev` |
| `DEMO_MODE=false` / SMTP | **FAIL** | email: “SMTP not configured; **demo mode active**”; `smtp_configured=false` |
| CORS allowlist | **PASS** | Preflight from `https://dxcon.com.vn` → ACAO + credentials |
| Example/docs completeness | **PASS** | `deployment/env/production.env.example` documents required keys |

### 5. Redis

| Item | Status | Evidence |
|------|--------|----------|
| Redis connectivity | **FAIL** | health startup check: `redis` **fail** — `Error -2 connecting to red-xxxxxxxxxxxxx:6379. Name or service not known.` (placeholder host) |

### 6. PostgreSQL

| Item | Status | Evidence |
|------|--------|----------|
| DB reachable | **PASS** | health `database: OK`, dialect `postgresql` |
| Migration readiness endpoint | **FAIL** | `/api/v1/system/ready` → **503** with migration error (stale startup / app-context bug on live) |

### 7. Storage

| Item | Status | Evidence |
|------|--------|----------|
| Local upload path writable on instance | **PASS** | startup storage check pass (`.../backend/uploads`) |
| Durable multi-node storage (S3) | **FAIL** | `storage_backend: local` on Render — uploads lost on redeploy / multi-instance |

### 8. Health endpoints

| Endpoint | Status | Evidence |
|----------|--------|----------|
| `/api/v1/system/live` | **PASS** | 200 `alive:true` |
| `/api/v1/system/liveness` | **PASS** | 200 |
| `/api/v1/system/health` | **WARNING** | 200 but overall DEGRADED (email/redis) |
| `/api/v1/system/ready` | **FAIL** | 503 `NOT_READY` (migrations error string) |

Code fix prepared locally for ready re-verify under request context (`backend/app/api/system/routes.py`) — **not live until redeploy**.

### 9. Backup

| Item | Status | Evidence |
|------|--------|----------|
| Runbooks/scripts present | **PASS** | `docs/BACKUP.md`, `BACKUP_RESTORE_RUNBOOK.md`, `deployment/scripts/backup_postgres.sh` |
| Operational backup verified on prod | **FAIL** | Dry-run rehearsal only; `pg_dump`/`pg_restore` **not found** in this environment; `DATABASE_URL` missing locally |

### 10. Restore

| Item | Status | Evidence |
|------|--------|----------|
| Documented restore procedure | **PASS** | runbook present |
| Restore rehearsal executed against staging/prod | **FAIL** | only `--dry-run`; no successful restore proof |

### 11. Logging

| Item | Status | Evidence |
|------|--------|----------|
| Structured JSON logs configured | **PASS** | health `log_format: json`; responses include `request_id` / `correlation_id` |

### 12. Monitoring

| Item | Status | Evidence |
|------|--------|----------|
| Probe endpoints available | **PASS** | live/health present |
| Alerting / Prometheus auth / on-call | **WARNING** | not independently verified in this session; metrics auth defaults improved in repo but live revision unknown |

### 13. Production build (web)

| Item | Status | Evidence |
|------|--------|----------|
| `apps/web` typecheck | **PASS** | exit 0 |
| `apps/web` production build | **PASS** | Next build success |
| Auth freeze verify | **PASS** | `verify:auth-freeze` PASS |

### 14. Flutter production build

| Item | Status | Evidence |
|------|--------|----------|
| `flutter test` | **PASS** | 36 tests passed |
| Production APK/IPA | **FAIL** | `No Android SDK found`; iOS not built |

### 15. Reception workflow

| Item | Status | Evidence |
|------|--------|----------|
| Frontend reception tests | **PASS** | 27 passed |
| Backend `test_reception_workspace` | **PASS** | 8/8 OK (incl. M4 handoff) |

### 16. Laboratory workflow

| Item | Status | Evidence |
|------|--------|----------|
| `tests.test_laboratory_workflow` | **PASS** | OK in suite with report/role tests |

### 17. Sample Collection

| Item | Status | Evidence |
|------|--------|----------|
| Collector/order lifecycle tests | **PASS** | `test_collector_operations` + `test_order_lifecycle` OK (7 tests in collector run) |

### 18. PDF Result

| Item | Status | Evidence |
|------|--------|----------|
| `tests.test_report_pdf` | **PASS** | OK |

### 19. Admin

| Item | Status | Evidence |
|------|--------|----------|
| Role dashboard admin API tests | **PASS** | `test_role_dashboards` OK |
| Live `/app/admin` | **PASS** | 307 to auth |

### 20. Patient Portal

| Item | Status | Evidence |
|------|--------|----------|
| Live `/app/patient` | **PASS** | 307 to auth |
| Deep patient inbox / PDF UX | **WARNING** | accepted limitation from RC (thin shells) |

---

## Critical security finding (P0)

| Item | Status | Evidence |
|------|--------|----------|
| Anonymous PHI API lock | **FAIL** | Live `GET https://api.dxcon.com.vn/api/v1/patients` returned **200** with patient list (`count: 60`). RC API auth gate (`b8e61fd`) is **not** active on the deployed revision. |

---

## Open P0 blockers (must clear before READY)

1. **Deploy RC commit** (`c3183a5`+) to Render with `BUILD_VERSION` / `GIT_SHA` / `APP_ENV=production`.
2. **Confirm API auth gate live** — anonymous `/api/v1/patients` must be **401**.
3. **Fix Redis** — real `REDIS_URL` (not `red-xxxxxxxxxxxxx` placeholder).
4. **`/ready` must return 200** after deploy of readiness fix + valid migrations.
5. **SMTP configured** and demo-mode messaging gone (`DEMO_MODE=false`).
6. **Durable storage** — S3 (or equivalent), not ephemeral local disk on Render.
7. **DNS for `app.dxcon.com.vn`** (or remove from CORS/product URLs).
8. **Backup + restore proof** on staging/prod Postgres (`pg_dump`/`pg_restore` available; restore rehearsal recorded).
9. **Flutter release artifacts** — Android SDK/signing + iOS build in CI or release machine.

Repo-side readiness fix for `/ready` is staged in working tree (`backend/app/api/system/routes.py`) and must be committed + deployed with the above.

---

## Declaration

```
DxCon v1.0.0 is NOT READY FOR PRODUCTION.
```

Re-run this report after P0 closure. Only then may Release Manager declare:

```
DxCon v1.0.0 READY FOR PRODUCTION.
```
