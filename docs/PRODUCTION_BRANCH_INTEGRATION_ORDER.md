# DxCon Production Branch Integration Order

**Release:** 8.1 · **Sprint:** 9
**Integration branch:** `release/8.1-production-integration`
**Base commit:** `456fabbea3ced2f91f4cc3bd5b628f42013691b4`

---

## Summary

All release branches form a **single linear stack**. The base commit already contains every sprint. No additional branch merges were performed during Sprint 9 — only verification, documentation, production guards, and smoke-test tooling were added on top.

---

## Base commit selection

| Item | Value |
| --- | --- |
| Production landing page commit (on `main`) | `b8ae528` — Release 3.0 Epic 10 |
| Fully integrated stack tip (Sprint 7) | `456fabb` — Release 8.0 Sprint 7 |
| Integration base chosen | `456fabb` (contains Sprints 1–8, preserves landing page from `main` lineage) |

The landing page (`apps/web/src/app/page.tsx` + `apps/web/src/components/landing/*`) is present and unchanged in purpose at the base commit.

---

## Integration order (verified dependency chain)

| # | Branch | Commit | Sprint | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 | `main` | `b8ae528` | Release 3.0 baseline | **ANCESTOR** | Production landing currently here |
| 1 | `release/6.0-auth-shell` | `d2add80` → `af69576` | Sprint 1–2 Auth + Workspaces | **VERIFIED_AND_MERGED** | Already in stack; login, AppShell, `/app/*` |
| 2 | `release/7.0-lims-core` | `52db081` | Sprint 3 LIMS Core | **VERIFIED_AND_MERGED** | `016_lims_core.sql`, lab workspace |
| 3 | `release/7.0-iot-logistics` | `60240f4` | Sprint 4 IoT Logistics | **VERIFIED_AND_MERGED** | `017_iot_logistics.sql`, cold chain |
| 4 | `release/7.0-analyzer-integration` | `b3e1c54` | Sprint 5 Analyzer | **VERIFIED_AND_MERGED** | `018_analyzer_integration.sql` |
| 5 | `release/8.0-clinical-workflow` | `b69e655` | Sprint 6 Clinical Governance | **VERIFIED_AND_MERGED** | `019_clinical_workflow.sql`, review queues |
| 6 | `release/8.0-patient-commerce` | `456fabb` | Sprint 7 Patient Commerce | **VERIFIED_AND_MERGED** | `020_patient_commerce.sql`, booking wizard |
| 7 | `feature/collector-lab-workflow` | `dd38d37` | Sprint 8 Collector/Lab | **VERIFIED_AND_MERGED** | 0 commits ahead of base; already absorbed |

---

## Branches rejected or deferred

| Branch | Reason |
| --- | --- |
| *(none)* | All known sprint branches are ancestors of the base commit |

---

## Conflict resolution

No merge conflicts occurred — linear history required no manual conflict resolution.

---

## Checks run at base commit (pre-Sprint 9 additions)

| Check | Status |
| --- | --- |
| Landing page present | ✅ |
| Domain middleware present | ✅ |
| Auth endpoints aligned frontend↔backend | ✅ |
| All workspace routes present | ✅ |
| Migrations 001–020 in order | ✅ |
| No duplicate route trees | ✅ |

---

## Sprint 9 additions on integration branch

- Production payment adapter guard (`get_payment_adapter` blocks non-production-ready adapters in strict envs)
- Documentation package (this file + 10 companion docs)
- Smoke test scripts (`apps/web/scripts/production-smoke-test.mjs`, `backend/scripts/production_api_smoke_test.py`)
- Security and migration reports under `generated-release/`

---

## Merge recommendation

Do **not** merge to `main` until:

1. Vercel production deploy from this branch passes smoke tests
2. Render backend deploy with explicit `CORS_ORIGINS` passes API smoke tests
3. Migrations 016–020 applied to staging DB and verified
4. Manual UAT cases UAT-01 through UAT-16 executed on staging
