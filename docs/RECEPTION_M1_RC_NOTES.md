# Reception Milestone 1 — Release Candidate Notes

**Candidate ID:** `reception-m1-rc`  
**Date (UTC):** 2026-07-25  
**Status:** READY FOR REVIEW (not auto-merged)  
**Git branch:** `feature/reception-m1`  
**Commit:** `7729a9c15c969372c699dd19e41a576bc4493026`  
**Base commit:** `21b89782621afc262b87c3d065fcb78f4253487c`  
**Protected release tip:** `origin/release/v1.0.0` @ `c3183a5` (unchanged by this candidate)

---

## Candidate purpose

Ship Reception Milestone 1 only:

Patient search/create → test catalog selection → authoritative pricing → laboratory order create → confirmation / reopen.

Explicitly **excludes** payment, barcode/QR, requisition, and lab handoff.

---

## Runtime files in candidate (committed)

| Path | Change |
|------|--------|
| `apps/web/src/app/app/reception/page.tsx` | M1 dashboard copy |
| `apps/web/src/app/app/reception/workflow/page.tsx` | M1 step orchestration |
| `apps/web/src/app/app/reception/workflow/Milestone1Steps.tsx` | Catalog / review / confirmation |
| `apps/web/src/app/app/reception/workflow/OrderSteps.tsx` | Patient step timeout / effect hardening |
| `apps/web/src/app/app/reception/workflow/Milestone1Steps.m1.test.tsx` | Focused M1 tests |

**Backend runtime:** none  
**Migrations:** none  
**Auth freeze paths:** none  
**Admin module:** none

---

## Quality gates (Release Manager)

| Gate | Result |
|------|--------|
| Frontend M1 Vitest (prior) | PASS (28/28 with OrderSteps.m1) |
| Auth freeze Vitest | PASS — 64 passed, 1 skipped |
| `verify:auth-freeze` | PASS |
| Admin module diff vs base | Empty |
| Files outside Reception (committed runtime) | None |
| Preview deploy | Recorded — `docs/RECEPTION_M1_DEPLOY_REPORT.md` (`dpl_B7ZjehRDMMwxLP6eDrti3MVTrinZ`) |
| Production verification | PASS (Release Manager acceptance) — see sign-off |

---

## Promote checklist (manual)

1. Open PR from `feature/reception-m1` into the agreed target branch (do **not** force into `release/v1.0.0` without owner approval).
2. Confirm CI auth-freeze + Reception tests green on the PR.
3. Deploy frontend to the intended environment.
4. Smoke Reception M1 happy path with synthetic data.
5. Tag only if release process requires a named RC tag (do **not** move existing RC tags).

---

## Rollback

Revert to previous frontend deployment / prior commit on the target branch. No DB migration rollback required for M1.

---

## References

- `docs/RECEPTION_M1_SIGNOFF.md`
- `docs/RECEPTION_M1_DEPLOY_REPORT.md`
- `docs/RECEPTION_M1_PRODUCTION_VERIFICATION.md`
- `docs/CHANGELOG.md` — `[Reception M1]`
- `docs/RELEASE_NOTES.md` — Reception Milestone 1 section
