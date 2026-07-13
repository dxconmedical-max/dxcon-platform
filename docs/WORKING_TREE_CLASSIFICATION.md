# Working Tree Classification — Release 8.1 Phase 1

**Branch:** `release/8.1-production-integration`
**HEAD:** `19a2931`
**Generated:** 2026-07-13

---

## Summary

- **82** modified tracked files + **29** untracked entries at start of Phase 1.
- **Zero** of them are uncommitted Release 8.1 code — all Release 8.1 work was already committed in `19a2931`.
- Remaining churn is **generated artifacts** + **pre-existing user work from a different release** (Master Data Foundation / Brand Assets).
- Per the workspace **release-isolation rule**, generated artifacts and other-release files are **not** committed under Release 8.1.

The result is an intentionally **not-fully-clean** working tree. Every remaining file is documented below.

---

## Classification

### REQUIRED_RELEASE_8_1 (committed in Phase 1 cleanup)

| File | Action |
|---|---|
| `.gitignore` | Extended for local archives, test output, upload scratch |
| `docs/WORKING_TREE_CLASSIFICATION.md` | This document |
| `generated-release/WORKING_TREE_CLASSIFICATION.json` | Machine-readable classification |

### GENERATED_ARTIFACT (already tracked; left uncommitted)

Regeneration noise from verification/report scripts. Already tracked in git, so not re-committed under 8.1:

- `apps/mobile/generated-release/*.json`
- `apps/web/generated-release/*.json`
- `backend/generated_api/{openapi.json,openapi.yaml,sdk/manifest.json}`
- `backend/generated_release/*.json` (82 modified + new UAT/brand reports)
- `deployment/reports/pre-deployment-report.json`

### LOCAL_TEST_OUTPUT (now gitignored)

- `generated-release/test_run_output.txt`
- `backend/generated_release/test_run_output.txt`
- `generated-release/PRODUCTION_API_SMOKE_REPORT.json`

### UNRELATED_LOCAL_FILE (now gitignored — never commit)

- `backend.zip` — 13 MB local repo snapshot
- `backend/uploads/reports/test.txt` — runtime scratch

### PRE_EXISTING_USER_WORK (different release — left untouched)

These belong to the **Master Data Foundation (Sprint-004)** / **Brand Assets** release, confirmed via `git log` (`ff61f15 Master Data Management Platform`). **Not deleted, not committed** under 8.1:

- `backend/app/mdm/security.py`
- `backend/migrations/002_uat_critical_fixes.sql`
- `backend/scripts/{generate_brand_assets,generate_uat_final_report,uat_lib,verify_master_data,verify_uat_*}.py`
- `backend/docs/PRODUCTION_SMOKE_TEST.md`
- `docs/BRAND_GUIDELINES.md`, `docs/REQUIRED_ENVIRONMENT_VARIABLES.md`
- `docs/sprints/SPRINT-004-MASTER-DATA-FOUNDATION.md`, `docs/srs/SPRINT-004-MASTER-DATA-FOUNDATION-SRS.md`
- `scripts/verify_master_data.py`
- `apps/mobile/lib/**/*.dart`, `apps/mobile/tool/verify_patient_collector_mvp.dart` (mobile app work)

### SENSITIVE_OR_SECRET — CRITICAL

| Path | Issue |
|---|---|
| `backend/uploads/results/*.pdf` | **Already committed to git history.** Filenames suggest **real patient names** and signed reports (e.g. `..._NGUYEN_THI_BICH_THAO.signed.pdf`). This is possible **PHI in version control**. |

**Blocker `CRIT-PHI-001`.** Remediation requires a git history rewrite (`git filter-repo` / BFG) and force-push — an **irreversible** action. Per mission rules, this is **not** performed automatically and is escalated for human decision.

Recommended remediation (for operator approval):
1. Confirm the PDFs contain real PHI.
2. Rotate any exposure; notify per data-policy if required.
3. Rewrite history to purge `backend/uploads/results/*.pdf`, force-push, and invalidate forks/clones.
4. Add `backend/uploads/` to `.gitignore` going forward (kept narrow to `backend/uploads/reports/` in this pass to avoid un-tracking the existing files before the decision is made).

---

## Resulting state

- Release 8.1 files: **all committed** (in `19a2931` + Phase-1 cleanup commit).
- Working tree: **NOT clean by design** — remaining entries are generated artifacts and other-release user work, intentionally preserved uncommitted.
- One **Critical** unresolved item: `CRIT-PHI-001` (PHI in history).
