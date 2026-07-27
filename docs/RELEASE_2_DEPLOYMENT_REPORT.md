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

## 4. Redis — SUPER_ADMIN diagnostic ready; production not cut over

**Invalid check (retained):** local DNS/TCP/PING of `red-*` → **NOT APPLICABLE**.

**New path:** `GET /api/v1/system/diagnostics/redis` (SUPER_ADMIN JWT, `Cache-Control: no-store`, sanitized errors only).

| Item | Status |
|------|--------|
| Implementation commit | `3544d62` pushed to `origin/release/v2.0.0` |
| Render production deploy | **BLOCKED** (no API key / deploy hook; Free plan has no shell) |
| Prod diagnostic HTTP | **404** |
| Deployment ID | **NONE** |
| API Redis | **NOT VERIFIED** (PASS only after `ping=true` from diagnostic) |
| Worker Redis | **NOT VERIFIED** |
| Scheduler Redis | **NOT VERIFIED** |
| Local DNS | **NOT APPLICABLE** |
| `REDIS_URL` changed | **No** |

---

## 5. Workers / scheduler — NOT VERIFIED for Redis

| Component | Observation |
|-----------|-------------|
| In-process scheduler | `status=pass`, `workers=4` (startup check) |
| Dedicated worker service in `render.yaml` | **Not present** |
| Worker / scheduler Redis broker | **NOT VERIFIED** |

---

## 6. Summary

| Layer | Result |
|-------|--------|
| Frontend login (production) | **PASS** (user-confirmed) |
| Post-login `/app/admin` | **PASS** |
| Auth bootstrap | **PASS** |
| CORS | **PASS** |
| `/register` nav prefetch | **FIXED** — public registration not in R2; Create account link removed |
| Local Redis DNS | **NOT APPLICABLE** |
| API Redis | **NOT VERIFIED** |
| Worker Redis | **NOT VERIFIED** |
| Scheduler Redis | **NOT VERIFIED** |
| Go-Live | **PARTIAL** (auth/shell); full M2 GA **not** claimed |
| Release 3 | **NOT STARTED** |

---

## References

- `backend/scripts/verify_release_2_redis.py`
- `docs/RELEASE_2_PRODUCTION_VERIFICATION.md`
- `docs/RELEASE_2_GO_LIVE_REPORT.md`
- `docs/RELEASE_2_DEPLOYMENT_CHECKLIST.md`
