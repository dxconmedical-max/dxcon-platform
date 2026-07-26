# Release 2 Deployment Report — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Operator:** Auto (Cursor) under Release 2 Go Live request  
**Git tip:** `15cc36fd2a0af7d589d277c40d18cfcccb494642` on `release/v2.0.0`  
**Remote:** `origin/release/v2.0.0` pushed (new branch)

---

## 1. Frontend (Vercel) — DONE

| Field | Value |
|-------|--------|
| Command | `npx vercel deploy --prod --yes --cwd .` |
| Commit meta | `15cc36fd2a0af7d589d277c40d18cfcccb494642` / `release/v2.0.0` |
| Deployment ID | `dpl_7vLhsf3nASxgM34mVQLdrtS6Sh6d` |
| Deployment URL | https://dxcon-platform-pwtaoc494-dxcon-med.vercel.app |
| Inspector | https://vercel.com/dxcon-med/dxcon-platform/7vLhsf3nASxgM34mVQLdrtS6Sh6d |
| Alias | **https://dxcon.com.vn** |
| Ready state | `READY` |
| Target | **production** |
| Build | M2 routes present in output (`/app/reception/m2/*`) |
| Wall clock | ~168s deploy phase (CLI session longer due to package resolve) |

---

## 2. Backend (Render) — NOT CUT OVER

| Item | Status |
|------|--------|
| Git push `release/v2.0.0` | **DONE** |
| `RENDER_API_KEY` / CLI deploy | **Unavailable** in this environment |
| `render.yaml` workers service | **None defined** (web + postgres only; `REDIS_URL` sync:false) |
| Live API tip | Still `2.5.0-dev` / `staging` / `git_sha=local` |
| M2 routes on API | **404** (code not running) |

**Ops action:** In Render dashboard, deploy `dxcon-api` from `release/v2.0.0` @ `15cc36f` (or merge/promote per service auto-deploy branch settings).

`BUILD_VERSION` in repo `backend/render.yaml` updated to `2.0.0-rc1` (takes effect on next Render deploy from this tip).

---

## 3. Migration — NOT APPLIED

Pending on production Postgres (no `DATABASE_URL` / Render shell in this session):

1. `backend/migrations/017_reception_receipts.sql`
2. `backend/migrations/018_lab_queue.sql`
3. `backend/migrations/019_sample_queue.sql`

Verify with `to_regclass(...)` per deployment checklist.

---

## 4. Redis — methodology corrected; API still FAIL (runtime)

**Invalid check removed:** local DNS/TCP/PING of Render internal `red-*` from Mac/CI (those hosts are private-network only → **NOT APPLICABLE**, not FAIL).

**Verifier:** `backend/scripts/verify_release_2_redis.py` (outside Render = HTTP only; inside Render = direct PING). Never prints `REDIS_URL` / credentials; hostname only as **`red-***`**.

| Component | Status | Notes |
|-----------|--------|-------|
| Local DNS | **NOT APPLICABLE** | Corrected false-negative methodology |
| **API Redis** | **FAIL** | Render-side startup check via `GET /api/v1/system/health`: `redis=fail`, sanitized `Error -2 connecting to red-***:6379`. Hostname class **`placeholder_x`**. `/health` HTTP **200** with `redis=DEGRADED` under `app_env=staging` is **not** Redis PASS. |
| **Worker Redis** | **NOT VERIFIED** | No worker in `render.yaml`; `/api/v1/system/workers` → 500 |
| **Scheduler Redis** | **NOT VERIFIED** | In-process scheduler pass ≠ Redis broker |
| Workspace / region / shared URL | **NOT VERIFIED** | No Render API access; blueprint has only `dxcon-api` + `REDIS_URL` `sync: false` |

**Ops action:** Confirm Internal Redis URL on `dxcon-api` in Render dashboard (do not change if already correct). Re-check **in Render** until startup `redis=pass`. Do not redeploy merely to test laptop DNS. Do not alter payment/queue/auth/migrations in this Redis correction.

---

## 5. Workers / scheduler — NOT VERIFIED for Redis

| Component | Observation |
|-----------|-------------|
| In-process scheduler | `status=pass`, `workers=4` (startup check) |
| Dedicated worker service in `render.yaml` | **Not present** |
| `GET /api/v1/system/workers` | **500** `INTERNAL_SERVER_ERROR` |
| Worker / scheduler Redis broker | **NOT VERIFIED** (do not collapse into whole-layer FAIL) |

---

## 6. Summary

| Layer | Result |
|-------|--------|
| Commit + push | **PASS** |
| Frontend production | **PASS** |
| Backend production tip | **FAIL / pending ops** |
| Migrations | **PENDING** |
| Local Redis DNS | **NOT APPLICABLE** |
| API Redis | **FAIL** |
| Worker Redis | **NOT VERIFIED** |
| Scheduler Redis | **NOT VERIFIED** |
| Workers process | **PARTIAL** (in-process only) |
| Go-Live | **NOT PASS** |

---

## References

- `backend/scripts/verify_release_2_redis.py`
- `docs/RELEASE_2_PRODUCTION_VERIFICATION.md`
- `docs/RELEASE_2_GO_LIVE_REPORT.md`
- `docs/RELEASE_2_DEPLOYMENT_CHECKLIST.md`
