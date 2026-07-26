# Release 2 Go-Live Report — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Branch / tip:** `release/v2.0.0` @ `15cc36f`  
**Overall:** **GO LIVE PARTIAL — FRONTEND LIVE; API CUTOVER REQUIRED**

---

## Executive summary

Reception M2 UI is **live on production** (`https://dxcon.com.vn`) from commit `15cc36f`, with all M2 routes auth-gated. The production API (`https://api.dxcon.com.vn`) is **not yet running this tip**: M2 endpoints return **404**, Redis health **fails**, and `/ready` returns **503**. Migrations `017`–`019` were **not** applied from this session.

Do **not** declare full Reception M2 GA until backend deploy + Redis + migrations are complete and production verification is re-run to PASS.

---

## What shipped this session

| Action | Result |
|--------|--------|
| Commit Reception M2 RC | `15cc36f` |
| Push `origin/release/v2.0.0` | **PASS** (new remote branch) |
| Vercel production deploy | **PASS** — `dpl_7vLhsf3nASxgM34mVQLdrtS6Sh6d` → `dxcon.com.vn` |
| Render API deploy | **NOT EXECUTED** (no Render API credentials; service not on R2 tip) |
| Postgres migrations 017–019 | **NOT EXECUTED** |
| Redis remediation | **NOT EXECUTED** (DNS fail observed) |
| Dedicated workers deploy | **N/A** — none in `render.yaml` |

---

## Verification snapshot

| Area | Result |
|------|--------|
| Frontend M2 routes | **PASS** (307 → login) |
| Auth freeze redirect | **PASS** |
| Payment / receipt / barcode / QR / queues (E2E) | **BLOCKED** — API tip missing R2 routes |
| Redis | **FAIL** |
| API ready | **FAIL** (503) |

Details: `docs/RELEASE_2_PRODUCTION_VERIFICATION.md`  
Deploy details: `docs/RELEASE_2_DEPLOYMENT_REPORT.md`

---

## Immediate ops checklist (to finish go-live)

1. [ ] Render: deploy `dxcon-api` from `release/v2.0.0` / `15cc36f`
2. [ ] Fix `REDIS_URL` (current host does not resolve)
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
| Full Reception M2 go-live? | **NO — blocked on API + Redis + migrations** |
| Safe to market as M2 live E2E? | **NO** until verification re-run PASS |

**STOP.**
