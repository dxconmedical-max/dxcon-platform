# Release 2 Production Verification — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Redis methodology correction (UTC):** 2026-07-26  
**Branch:** `release/v2.0.0` @ `15cc36fd2a0af7d589d277c40d18cfcccb494642`  
**Verdict:** **CONDITIONAL / PARTIAL** — Frontend production live; Backend tip / migrations / full Redis PASS not complete  
**Go-Live:** **NOT PASS** (do not mark live)

---

## Redis verification — corrected methodology

### Root cause of prior false negative

Earlier “Redis FAIL — hostname does not resolve” conclusions mixed **local DNS/TCP/PING** (Mac / Cursor sandbox) against a Render **internal** `red-*` hostname. Internal Key Value hosts are **not** expected to resolve outside the matching Render workspace/region. That local check is **invalid** as production Redis evidence.

**Invalid check removed:** local `getaddrinfo` / `nc` / `redis.PING` against `red-*` from outside Render.  
**Replacement:** `backend/scripts/verify_release_2_redis.py` (environment-aware).

| Check | Status |
|-------|--------|
| Local DNS of `red-*` | **NOT APPLICABLE** |
| Local TCP/TLS to `red-*` | **NOT APPLICABLE** |
| Local Redis PING | **NOT APPLICABLE** |

Credentials / full `REDIS_URL` are never printed. Hostname shown only as **`red-***`**.

### Runtime evidence (indirect, outside Render)

Probe tool: `python backend/scripts/verify_release_2_redis.py` → `backend/generated_release/RELEASE_2_REDIS_VERIFY.json`

| Component | Status | Evidence |
|-----------|--------|----------|
| **API Redis** | **FAIL** | `GET /api/v1/system/health` startup check `redis=fail` (executed **inside** the Render API process). Detail (sanitized): `Error -2 connecting to red-***:6379. Name or service not known.` Hostname class from error: **`placeholder_x`** (`red-` + repeated `x`, len 17) — not a typical live Render KV id. |
| **Worker Redis** | **NOT VERIFIED** | No dedicated worker service in `render.yaml`; `GET /api/v1/system/workers` → **500**. Do not mark whole Redis layer FAIL for this alone. |
| **Scheduler Redis** | **NOT VERIFIED** | In-process `scheduler` startup check **pass** (`workers:4`) — not Redis-broker evidence. |
| Local DNS | **NOT APPLICABLE** | Corrected; must not be recorded as FAIL. |

| Endpoint | HTTP | Redis-related |
|----------|------|----------------|
| `GET /health` | **200** | `status=OK`, `redis=DEGRADED`, `app_env=staging` (Redis not required when non-production) |
| `GET /api/v1/system/health` | **200** | overall **DEGRADED**; startup `redis=fail` |
| `GET /api/v1/system/ready` | **503** | `NOT_READY` (migrations context error; not used alone as Redis PASS) |
| `GET /api/v1/monitoring-center/redis` | **200** | ping **DEGRADED** / unavailable (same sanitized DNS error) |

**Operator claim:** Render logs show “Redis connection verified.” This session has **no Render log API access** to confirm. Codebase emits **`database connection verified`**, not a Redis equivalent — treat operator log claim as **unconfirmed** here. Public runtime health still shows API Redis **FAIL**.

**Workspace / region / shared `REDIS_URL`:** `render.yaml` defines only `dxcon-api` + Postgres; `REDIS_URL` is `sync: false` (dashboard). No worker/scheduler services to compare. Same-workspace / same-region / shared source: **NOT VERIFIED** from this environment (no Render API key). Do not alter `REDIS_URL`.

### Payment → Sample E2E

**Still BLOCKED** (independent of Redis methodology): API tip not R2 (`2.5.0-dev` / `staging` / `git_sha=local`); M2 routes **404**; migrations `017`–`019` not applied. Redis API FAIL remains an additional blocker until startup `redis=pass`.

---

## Environment probes

| Check | Result | Evidence |
|-------|--------|----------|
| Web `https://dxcon.com.vn` | **PASS** | HTTP 200 (login) |
| Web M2 routes | **PASS** | `/app/reception/m2/*` → **307** login |
| API health | **DEGRADED** | HTTP 200; startup DEGRADED |
| API ready | **FAIL** | HTTP **503** |
| API build identity | **NOT R2** | `version=2.5.0-dev`, `environment=staging`, `git_sha=local` |
| API Redis | **FAIL** | Startup check fail (see above) — **not** a local-DNS FAIL |
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
