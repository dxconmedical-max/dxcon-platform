# Release 2 Production Verification — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Redis methodology correction (UTC):** 2026-07-26  
**Branch:** `release/v2.0.0` @ `15cc36fd2a0af7d589d277c40d18cfcccb494642`  
**Verdict:** **CONDITIONAL / PARTIAL** — Frontend production live; Backend tip / migrations / full Redis PASS not complete  
**Go-Live:** **NOT PASS** (do not mark live)

---

## Redis verification — SUPER_ADMIN in-runtime diagnostic

### Architecture (existing)

| Surface | Path | Auth |
|---------|------|------|
| Liveness/health | `/health`, `/api/v1/system/health` | Public |
| Ready | `/ready`, `/api/v1/system/ready`, `/api/v1/system/readiness` | Public |
| Monitoring redis | `/api/v1/monitoring-center/redis` | Unauthenticated (reports status; may include error text) |
| **New diagnostic** | **`GET /api/v1/system/diagnostics/redis`** | **SUPER_ADMIN JWT only** (`roles_required`) |

Redis client: `app.config["REDIS_URL"]` via `redis.from_url` (same pattern as `check_redis` / `check_redis_health`). No new secret source. Local DNS of `red-*` = **NOT APPLICABLE**.

### Deploy / production call (2026-07-26)

| Step | Result |
|------|--------|
| Code commit | `3544d62` on `release/v2.0.0` (pushed) |
| Render deploy | **BLOCKED** — no `RENDER_API_KEY` / deploy hook in this environment; Free instance has no Dashboard Shell |
| Production tip | Still `2.5.0-dev` / `staging` / `git_sha=local` |
| Diagnostic route on prod | **404** (not deployed yet) |
| Sanitized production diagnostic response | **N/A** — endpoint not live |
| Deployment ID | **NONE** |

### Component status

| Component | Status |
|-----------|--------|
| **API Redis** | **NOT VERIFIED** — requires deployed diagnostic with `ping=true` |
| **Worker Redis** | **NOT VERIFIED** |
| **Scheduler Redis** | **NOT VERIFIED** |
| **Local DNS** | **NOT APPLICABLE** |

**Go-Live:** **NOT PASS**

After Render deploy of `3544d62` (or later tip containing the diagnostic):

```bash
# SUPER_ADMIN access token only — never print token/REDIS_URL
export DXCON_SUPER_ADMIN_TOKEN='…'
curl -sS -H "Authorization: Bearer ${DXCON_SUPER_ADMIN_TOKEN}" \
  -H "Cache-Control: no-store" \
  https://api.dxcon.com.vn/api/v1/system/diagnostics/redis
# PASS only if: {"service":"redis","status":"ok","ping":true,"runtime":"render",...}
python backend/scripts/verify_release_2_redis.py
```

---

## Environment probes

| Check | Result | Evidence |
|-------|--------|----------|
| Web `https://dxcon.com.vn` | **PASS** | HTTP 200 (login) |
| Web M2 routes | **PASS** | `/app/reception/m2/*` → **307** login |
| API health | **DEGRADED** | HTTP 200; startup DEGRADED |
| API ready | **FAIL** | HTTP **503** |
| API build identity | **NOT R2** | `version=2.5.0-dev`, `environment=staging`, `git_sha=local` |
| API Redis | **NOT VERIFIED** | Diagnostic not deployed (prod 404); local DNS N/A |
| Worker Redis | **NOT VERIFIED** | No dedicated worker |
| Scheduler Redis | **NOT VERIFIED** | In-process only |
| Local Redis DNS | **NOT APPLICABLE** | — |
| M2 API routes | **FAIL (not deployed)** | lab/sample/qr/barcode → **404** |
| Legacy reception API | **UP** | **401** without auth |

---

## Feature verification

| Domain | Frontend route | Backend capability | Result |
|--------|----------------|--------------------|--------|
| Payment | `/app/reception/m2/payment` live | Collect APIs on old tip only | **PARTIAL** |
| Receipt | `/app/reception/m2/receipt` live | Needs migration `017` + engine | **BLOCKED** |
| Barcode | `/app/reception/m2/barcode` live | `/barcode/printers` 404 | **BLOCKED** |
| QR | `/app/reception/m2/qr` live | `/qr/kinds` 404 | **BLOCKED** |
| Lab queue | `/app/reception/m2/lab-queue` live | `/lab-queue` 404 | **BLOCKED** |
| Sample queue | `/app/reception/m2/sample-queue` live | `/sample-queue` 404 | **BLOCKED** |

---

## Auth freeze

Unauthenticated M2 pages redirect to `/login?next=…` — auth middleware preserved.

---

## Required to reach full PASS

1. Deploy API from `origin/release/v2.0.0` (`15cc36f`) on Render.
2. Ensure `dxcon-api` `REDIS_URL` is the real Render **Internal** Redis URL (not a placeholder). Confirm **in Render** via startup `redis=pass` or `verify_release_2_redis.py` with `RENDER=true`. Do **not** validate by resolving `red-*` from a laptop.
3. Apply migrations `017`–`019` on production Postgres.
4. Set `BUILD_VERSION=2.0.0-rc1`, prefer `APP_ENV=production`.
5. Re-run verification (M2 routes **401** unauth / **200** with reception JWT).

---

## References

- `backend/scripts/verify_release_2_redis.py`
- `docs/RELEASE_2_DEPLOYMENT_REPORT.md`
- `docs/RELEASE_2_GO_LIVE_REPORT.md`
- `docs/RELEASE_2_RC_REPORT.md`
