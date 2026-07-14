# Release 8 Finalization

**Family:** Release 8.0 + Release 8.1  
**Branch:** `release/8.1-production-integration`  
**Code-freeze tag:** `release/8.1-code-freeze`  
**Finalized:** 2026-07-14  
**Decision:** **CODE FREEZE COMPLETE** — production cutover remains blocked on external actions

---

## Scope delivered (in code)

| Sprint | Scope | Branch tip absorbed |
|---|---|---|
| 6 | Clinical workflow & result governance | `b69e655` |
| 7 | Patient commerce | `456fabb` |
| 8 | Collector/lab workflow (prior stack) | ancestor of tip |
| 9 | Production web integration & validation docs/smoke | `19a2931` |
| 8.1 blockers | Duplicate-route fix, CORS hardening, staging prep | `069cb8c` |

---

## Code freeze status

| Gate | Status |
|---|---|
| CODE_READY | **PASS** |
| STAGING_CONFIG_READY | **PASS** |
| STAGING_DEPLOYED | **BLOCKED_EXTERNAL_ACTION** |
| MIGRATIONS_APPLIED_STAGING | **NOT_STARTED** |
| SMOKE_PASS | **FAIL** (until deploy + CORS_ORIGINS fix) |
| UAT_PASS | **NOT_STARTED** |
| PRODUCTION_READY | **NOT_STARTED** |
| Merge to `main` | **DO NOT MERGE** until staging smoke + UAT pass |

---

## What “finalized” means here

1. No further Release 8 product features on this branch without a new revision.  
2. Tip commit is the integration candidate for staging deploy.  
3. Production is **not** live for Sprint 6/7 capabilities.  
4. Remaining work is **operator/infra**, not code invention.

---

## External actions required before production cutover

1. Set Render `CORS_ORIGINS` to production apex/www/app hosts.  
2. Stand up staging (Postgres, Redis, Render, Vercel, DNS).  
3. Apply migrations 016–020 on **staging** only.  
4. Run staging smoke + UAT-01..16.  
5. Add `app.dxcon.com.vn` (and staging domains) using provider-displayed DNS targets.  
6. Resolve `CRIT-PHI-001` (possible PHI in git history) before advertising a clean production baseline.

---

## Artifacts

- `generated-release/RELEASE_8_CERTIFICATE.json`  
- `generated-release/BLOCKER_RESOLUTION_EXIT_STATES.json`  
- `docs/PRODUCTION_INTEGRATION_CURRENT_STATE.md`  
- `docs/STAGING_DEPLOYMENT_RUNBOOK.md`  
- `docs/STAGING_ENVIRONMENT_VARIABLES.md`  
- `docs/MIGRATIONS_016_020_STAGING_RUNBOOK.md`  
- `docs/STAGING_UAT_EXECUTION.md`  
- `docs/API_403_ROOT_CAUSE.md`  
- `docs/BACKEND_TEST_FAILURE_RESOLUTION.md`

---

## Rollback of this freeze

To continue development: create `release/8.2-*` from tag `release/8.1-code-freeze`. Do not reopen Release 8 product scope on the frozen tip without renaming the release.
