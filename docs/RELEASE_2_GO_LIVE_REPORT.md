# Release 2 Go-Live Report — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Overall:** **PARTIAL GO-LIVE** — production frontend auth + admin shell verified  
**Go-Live decision:** **PARTIAL** (not full Reception M2 GA; **do not start Release 3**)

---

## Executive summary

User-confirmed production:

- Login **PASS** on `https://dxcon-platform.vercel.app`
- `/app/admin` **PASS**
- Auth bootstrap **PASS** (`authenticated` / cookies / session)
- CORS **PASS**; Admin KPIs load

Public self-registration is **not** part of Release 2. The login “Create account” link to missing `/register` caused Next.js prefetch **404** — link removed (nav-only; auth state machine unchanged).

Redis remains component-split: API / Worker / Scheduler **NOT VERIFIED**; Local DNS **NOT APPLICABLE**.

---

## Verification snapshot

| Area | Result |
|------|--------|
| Frontend login | **PASS** |
| Post-login admin shell | **PASS** |
| Auth bootstrap | **PASS** |
| CORS | **PASS** |
| `/register` prefetch 404 | **FIXED** (link removed) |
| API Redis | **NOT VERIFIED** |
| Worker Redis | **NOT VERIFIED** |
| Scheduler Redis | **NOT VERIFIED** |
| Local Redis DNS | **NOT APPLICABLE** |
| Full M2 E2E | **NOT COMPLETE** |
| Release 3 | **NOT STARTED** |

---

## Decision

| Question | Answer |
|----------|--------|
| Frontend auth go-live? | **YES** (verified) |
| Full Reception M2 go-live? | **NO — PARTIAL** |
| Safe to start Release 3? | **NO** |
| API Redis PASS? | **NO — NOT VERIFIED** |

**STOP** after this finalize. Remaining Redis/worker/scheduler and M2 API cutover stay open.
