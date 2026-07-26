# Release 2 Production Verification — Reception M2 (`2.0.0-rc1`)

**Date (UTC):** 2026-07-26  
**Branch:** `release/v2.0.0` @ `15cc36fd2a0af7d589d277c40d18cfcccb494642`  
**Verdict:** **CONDITIONAL / PARTIAL** — Frontend production live; Backend/Redis/migrations not cut over

---

## Environment probes

| Check | Result | Evidence |
|-------|--------|----------|
| Web `https://dxcon.com.vn` | **PASS** | HTTP 200 (login) |
| Web M2 routes | **PASS** | All `/app/reception/m2/*` → **307** login (auth gate intact) |
| API health `api.dxcon.com.vn` | **DEGRADED** | HTTP 200; `status=DEGRADED` |
| API ready | **FAIL** | HTTP **503** `NOT_READY` |
| API build identity | **NOT R2** | `version=2.5.0-dev`, `environment=staging`, `git_sha=local` |
| Redis | **FAIL** | `Error -2 connecting to red-xxxxxxxxxxxxx:6379` |
| Scheduler / workers | **PARTIAL** | `scheduler` pass with `workers:4`; Redis dependency fail |
| M2 API routes | **FAIL (not deployed)** | `/lab-queue`, `/sample-queue`, `/qr/kinds`, `/barcode/printers` → **404** |
| Legacy reception API | **UP** | `/dashboard`, `/tests` → **401** (auth required; routes exist) |

---

## Feature verification

| Domain | Frontend route | Backend capability | Result |
|--------|----------------|--------------------|--------|
| Payment | `/app/reception/m2/payment` live | Collect APIs on old tip only | **PARTIAL** — UI live; R2 engine not on API tip |
| Receipt | `/app/reception/m2/receipt` live | Needs migration `017` + engine | **BLOCKED** |
| Barcode | `/app/reception/m2/barcode` live | `/barcode/printers` 404 | **BLOCKED** |
| QR | `/app/reception/m2/qr` live | `/qr/kinds` 404 | **BLOCKED** |
| Lab queue | `/app/reception/m2/lab-queue` live | `/lab-queue` 404 | **BLOCKED** |
| Sample queue | `/app/reception/m2/sample-queue` live | `/sample-queue` 404 | **BLOCKED** |

Authenticated end-to-end collect/print/advance was **not** executed against production because the API tip does not contain R2 M2 routes.

---

## Auth freeze

Unauthenticated M2 pages redirect to `/login?next=…` — auth middleware behavior preserved.

---

## Required to reach full PASS

1. Deploy API from `origin/release/v2.0.0` (`15cc36f`) on Render (`dxcon-api` / `dxcon-ap`).
2. Set/fix `REDIS_URL` to a resolvable Redis instance (current hostname fails DNS).
3. Apply migrations `017`–`019` on production Postgres.
4. Set `BUILD_VERSION=2.0.0-rc1`, prefer `APP_ENV=production`.
5. Re-run this verification matrix (expect M2 routes **401** without token, **200** with reception JWT).

---

## References

- `docs/RELEASE_2_DEPLOYMENT_REPORT.md`
- `docs/RELEASE_2_GO_LIVE_REPORT.md`
- `docs/RELEASE_2_RC_REPORT.md`
