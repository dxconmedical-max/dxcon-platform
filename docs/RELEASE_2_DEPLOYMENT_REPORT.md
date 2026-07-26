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

## 4. Redis — FAIL (pre-existing / config)

Health check reports Redis configured but **DNS failure** to `red-xxxxxxxxxxxxx:6379`.

**Ops action:** Replace `REDIS_URL` with a valid Render Redis / Upstash / managed URL; re-check `/api/v1/system/health`.

---

## 5. Workers — PARTIAL

| Component | Observation |
|-----------|-------------|
| In-process scheduler | `status=pass`, `workers=4` |
| Dedicated worker service in `render.yaml` | **Not present** |
| Redis-backed jobs | **Blocked** by Redis DNS fail |

No separate worker deploy was possible from this checklist without a Render worker service + working Redis.

---

## 6. Summary

| Layer | Result |
|-------|--------|
| Commit + push | **PASS** |
| Frontend production | **PASS** |
| Backend production tip | **FAIL / pending ops** |
| Migrations | **PENDING** |
| Redis | **FAIL** |
| Workers | **PARTIAL** |

---

## References

- `docs/RELEASE_2_PRODUCTION_VERIFICATION.md`
- `docs/RELEASE_2_GO_LIVE_REPORT.md`
- `docs/RELEASE_2_DEPLOYMENT_CHECKLIST.md`
