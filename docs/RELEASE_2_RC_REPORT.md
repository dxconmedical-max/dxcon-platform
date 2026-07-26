# Release 2 RC Report — Reception M2 Freeze

**Candidate ID:** `release-2-reception-m2-rc`  
**Version:** `2.0.0-rc1`  
**Date (UTC):** 2026-07-26T07:38:13Z  
**Branch:** `release/v2.0.0`  
**Base freeze tip (R1):** `cda364d5e19f3db28bd0eb028b9fd9dad4b72169`  
**Status:** **RC READY FOR REVIEW** — Reception M2 product track frozen for RC; not yet GA  

**Auth freeze:** Active — no auth runtime paths modified for this RC.

---

## Scope frozen in this RC

Reception M2 on Release 2:

| Step | Module | Status |
|------|--------|--------|
| 3 | Payment Engine | Implemented |
| 4 | Receipt Module | Implemented |
| 5 | Barcode Module | Implemented |
| 6 | QR Module | Implemented |
| 7 | Laboratory Queue | Implemented |
| 8 | Sample Queue | Implemented |

**Out of scope for this RC / later R2 milestones:** Laboratory deep workflow (M7), Collector mobile (M8/M11), Doctor track, live VNPay settlement, Alembic migration runner.

---

## Quality gates (executed 2026-07-26)

| Gate | Command / suite | Result |
|------|-----------------|--------|
| Typecheck | `apps/web` `npm run typecheck` | **PASS** |
| Lint (Reception M2) | `eslint src/modules/reception-m2` | **PASS** |
| Lint (full web) | `npm run lint` | **RESIDUAL** — 10 errors outside M2 (auth-freeze surfaces + collector/lab pages). Auth paths not changed. npm exit code 0. |
| Auth regression | `npm run test:auth-freeze` | **PASS** — 64 passed, 1 skipped |
| Auth freeze guard | `npm run verify:auth-freeze` | **PASS** |
| Reception frontend tests | `vitest` reception + handoff/documents | **PASS** — 50 passed |
| Production build | `npm run build` | **PASS** — includes `/app/reception/m2/*` routes |
| Payment regression | `tests.test_payment_engine` | **PASS** (in engine suite) |
| Receipt regression | `tests.test_receipt_engine` | **PASS** |
| Barcode regression | `tests.test_barcode_engine` | **PASS** |
| QR regression | `tests.test_qr_engine` | **PASS** |
| Lab queue regression | `tests.test_lab_queue_engine` | **PASS** |
| Sample queue regression | `tests.test_sample_queue_engine` | **PASS** |
| Engine suite aggregate | payment+receipt+barcode+qr+lab+sample | **PASS** — 18 tests |
| Reception workspace | `tests.test_reception_workspace` | **PASS** — 8 tests |

---

## Surfaces

### Web (M2)

- `/app/reception/m2` hub
- `/app/reception/m2/payment`
- `/app/reception/m2/receipt`
- `/app/reception/m2/barcode`
- `/app/reception/m2/qr`
- `/app/reception/m2/lab-queue`
- `/app/reception/m2/sample-queue`

### Backend engines

- `payment_engine.py`, `receipt_engine.py` (+ PDF)
- `barcode_engine.py`, `printers.py`
- `qr_engine.py`
- `lab_queue_engine.py`, `sample_queue_engine.py`

### Migrations (additive SQL)

- `017_reception_receipts.sql`
- `018_lab_queue.sql`
- `019_sample_queue.sql`

---

## Freeze rules (RC)

1. No new Reception M2 feature work on this RC without Release Manager exception.
2. Auth freeze remains absolute (`docs/AUTH_FREEZE.md`).
3. Release 1 remains hotfix-only (`docs/RELEASE_1_FREEZE.md`).
4. Prefer named commits / PR into `release/v2.0.0` before production promote.
5. Apply migrations `017`–`019` before enabling M2 receipt/queue tables in production.

---

## Known residuals

| Item | Notes |
|------|--------|
| Full-repo ESLint | Pre-existing errors in auth-freeze files + collector/lab pages — not introduced by M2 engines; do not “fix” via auth edits |
| Working tree | R2 M2 implementation may still be uncommitted relative to `cda364d` tip — commit/PR before deploy |
| VNPay | Sandbox / compact QR only — no live settlement |
| Lab M7 depth | Accession/validation beyond queue stages deferred |

---

## Promote / next

1. Commit or PR Reception M2 exclusive files (+ shared wiring) per release isolation.
2. Follow `docs/RELEASE_2_DEPLOYMENT_CHECKLIST.md`.
3. Execute `docs/RELEASE_2_GO_LIVE_CHECKLIST.md` smoke.
4. Tag `v2.0.0-rc1` only after RM approval (do not move R1 tags).

## References

- `docs/RELEASE_2_RC_NOTES.md`
- `docs/RELEASE_2_GO_LIVE_CHECKLIST.md`
- `docs/RELEASE_2_DEPLOYMENT_CHECKLIST.md`
- `docs/RELEASE_2_ROADMAP.md`
- Module docs: `PAYMENT_ENGINE.md`, `RECEIPT_MODULE.md`, `BARCODE_MODULE.md`, `QR_MODULE.md`, `LAB_QUEUE_MODULE.md`, `SAMPLE_QUEUE_MODULE.md`
