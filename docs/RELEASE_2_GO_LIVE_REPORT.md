# Release 2 Go-Live Report — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Branch / tip:** `release/v2.0.0` @ `15cc36f`  
**Overall:** **GO LIVE PARTIAL — FRONTEND LIVE; API CUTOVER REQUIRED**  
**Go-Live decision:** **NOT PASS**

---

## Executive summary

Reception M2 UI is **live on production** (`https://dxcon.com.vn`) from commit `15cc36f`, with all M2 routes auth-gated. The production API (`https://api.dxcon.com.vn`) is **not yet running this tip**: M2 endpoints return **404**, and `/api/v1/system/ready` returns **503**. Migrations `017`–`019` were **not** applied from the go-live session.

**Redis methodology correction:** Prior “Redis FAIL because hostname does not resolve” from **local** DNS/TCP/PING of Render internal `red-*` is **invalid**. Local DNS = **NOT APPLICABLE**.  

**Current Redis status (separate components):**

| Component | Status |
|-----------|--------|
| API Redis | **FAIL** (Render process startup check via public health; sanitized host `red-***`, class `placeholder_x`) |
| Worker Redis | **NOT VERIFIED** |
| Scheduler Redis | **NOT VERIFIED** |
| Local DNS | **NOT APPLICABLE** |

Payment → Sample E2E remains **BLOCKED** (API tip + migrations; API Redis still FAIL).

Do **not** declare full Reception M2 GA until backend deploy + Redis PASS (in-Render) + migrations complete and verification is re-run.

---

## What shipped this session

| Action | Result |
|--------|--------|
| Commit Reception M2 RC | `15cc36f` |
| Push `origin/release/v2.0.0` | **PASS** (new remote branch) |
| Vercel production deploy | **PASS** — `dpl_7vLhsf3nASxgM34mVQLdrtS6Sh6d` → `dxcon.com.vn` |
| Render API deploy | **NOT EXECUTED** (no Render API credentials; service not on R2 tip) |
| Postgres migrations 017–019 | **NOT EXECUTED** |
| Redis methodology | **CORRECTED** — env-aware verifier; local DNS N/A |
| Redis API runtime | **Still FAIL** on public health startup check |
| Dedicated workers deploy | **N/A** — none in `render.yaml` |

---

## Verification snapshot

| Area | Result |
|------|--------|
| Frontend M2 routes | **PASS** (307 → login) |
| Auth freeze redirect | **PASS** |
| Payment / receipt / barcode / QR / queues (E2E) | **BLOCKED** — API tip missing R2 routes |
| API Redis | **FAIL** |
| Worker Redis | **NOT VERIFIED** |
| Scheduler Redis | **NOT VERIFIED** |
| Local Redis DNS | **NOT APPLICABLE** |
| API ready | **FAIL** (503) |
| Go-Live | **NOT PASS** |

Details: `docs/RELEASE_2_PRODUCTION_VERIFICATION.md`  
Deploy details: `docs/RELEASE_2_DEPLOYMENT_REPORT.md`  
Verifier: `backend/scripts/verify_release_2_redis.py`

---

## Immediate ops checklist (to finish go-live)

1. [ ] Render: deploy `dxcon-api` from `release/v2.0.0` / `15cc36f`
2. [ ] Confirm `REDIS_URL` Internal URL on `dxcon-api` (verify **in Render** / startup `redis=pass` — **not** via laptop DNS)
3. [ ] Run SQL migrations `017`, `018`, `019`
4. [ ] Confirm `BUILD_VERSION=2.0.0-rc1` and prefer `APP_ENV=production`
5. [ ] Re-probe M2 APIs → expect **401** unauth / **200** with reception token
6. [ ] Execute smoke from `docs/RELEASE_2_GO_LIVE_CHECKLIST.md` (payment → sample queue)
7. [ ] Update this report to **PASS** and tag `v2.0.0-rc1` if process requires

---

## Rollback

| Layer | Action |
|-------|--------|
| Frontend | Redeploy previous Vercel production deployment (pre-`dpl_7vLhsf3n…`) |
| Backend | No R2 tip change applied — no API rollback needed for this session |
| DB | No R2 migrations applied — no schema rollback needed |

---

## Decision

| Question | Answer |
|----------|--------|
| Frontend go-live? | **YES** |
| Full Reception M2 go-live? | **NO — blocked on API tip + API Redis + migrations** |
| Safe to market as M2 live E2E? | **NO** until verification re-run PASS |
| Local Redis DNS used as FAIL? | **NO — retracted (NOT APPLICABLE)** |
| API Redis PASS? | **NO** |
| Payment → Sample E2E unblocked? | **NO** |

**STOP.** Go-Live remains **NOT PASS**.
