# Production Migration Runbook

**Release:** 8.1 · **Sprint:** 9
**Do not execute production migrations automatically.**

---

## Overview

20 additive migrations (`001`–`020`) are required for the full integrated stack. All are present in the base commit. Migrations use `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` — idempotent and non-destructive.

**Apply in strict numeric order.** Do not skip or reorder.

---

## Pre-migration checklist

- [ ] Full database backup taken and verified
- [ ] Staging migration rehearsal completed successfully
- [ ] Maintenance window communicated (if needed)
- [ ] Rollback plan documented (see per-migration rollback below)
- [ ] Application deployed with code that matches migration version

---

## Migration inventory

| # | File | Branch/Sprint | Purpose | Type | Lock risk | Production ready |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | `001_business_engine_sprint1.sql` | Sprint 1 | Business engine core tables (`biz_orders`, etc.) | Additive CREATE | Low | ✅ (likely already applied on prod) |
| 002 | `002_uat_critical_fixes.sql` | UAT fixes | Audit log `request_id`, order barcode columns | Additive ALTER | Low | ✅ |
| 003 | `003_mdm_foundation.sql` | MDM | Master data import batches | Additive CREATE | Low | ✅ |
| 004 | `004_partner_foundation.sql` | Sprint 5 | Organizations, partners, memberships | Additive CREATE | Low | ✅ |
| 005 | `005_reception_workspace.sql` | Sprint 6 | Reception queue extensions | Additive ALTER | Low | ✅ |
| 006 | `006_lab_workspace.sql` | Sprint 7 | Lab collection condition fields | Additive ALTER | Low | ✅ |
| 007 | `007_reporting_engine.sql` | Sprint 8 | Clinical reports table | Additive CREATE | Low | ✅ |
| 008 | `008_portal.sql` | Sprint 9 | Portal notifications | Additive CREATE | Low | ✅ |
| 009 | `009_executive_platform.sql` | Sprint 10 | Launch checklist items | Additive CREATE | Low | ✅ |
| 010 | `010_operations_center.sql` | Release 1.0 | Support tickets | Additive CREATE | Low | ✅ |
| 011 | `011_integration_platform.sql` | Epic 3.5 | Integration connectors | Additive CREATE | Low | ✅ |
| 012 | `012_patient_marketplace.sql` | Epic 5 | Marketplace providers, listings | Additive CREATE | Low | ✅ |
| 013 | `013_mobile_mvp.sql` | Epic 7 | Mobile devices | Additive CREATE | Low | ✅ |
| 014 | `014_pilot_readiness.sql` | Epic 8 | Pilot onboarding sessions | Additive CREATE | Low | ✅ |
| 015 | `015_ai_platform_core.sql` | Epic 9 | AI platform providers | Additive CREATE | Low | ✅ |
| 016 | `016_lims_core.sql` | Sprint 3 (7.0) | Specimens, accession, LIMS core | Additive CREATE | Medium (new tables) | ✅ — **apply before Sprint 3 deploy** |
| 017 | `017_iot_logistics.sql` | Sprint 4 (7.0) | IoT device extensions, cold chain | Additive ALTER | Low | ✅ |
| 018 | `018_analyzer_integration.sql` | Sprint 5 (7.0) | Analyzer metadata columns | Additive ALTER | Low | ✅ |
| 019 | `019_clinical_workflow.sql` | Sprint 6 (8.0) | Result governance columns | Additive ALTER | Low | ✅ — **apply before Sprint 6 deploy** |
| 020 | `020_patient_commerce.sql` | Sprint 7 (8.0) | Marketplace commerce extensions | Additive ALTER | Low | ✅ — **apply before Sprint 7 deploy** |

---

## Execution (staging or production)

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dxcon"

for f in backend/migrations/0*.sql; do
  echo "Applying $f ..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

For incremental production apply (only new migrations since last deploy):

```bash
# Example: if 001-015 already applied, apply only 016-020
for f in backend/migrations/01{6,7,8,9}_*.sql backend/migrations/020_*.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

---

## Verification queries (post-migration)

```sql
-- LIMS core (016)
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'specimens';

-- Clinical workflow (019)
SELECT column_name FROM information_schema.columns
  WHERE table_name = 'biz_result_items' AND column_name = 'specimen_id';

-- Patient commerce (020)
SELECT column_name FROM information_schema.columns
  WHERE table_name = 'mp_providers' AND column_name = 'featured';
```

---

## Rollback approach

All migrations are additive. Rollback strategy:

1. **Forward-fix preferred** — deploy a corrective migration rather than dropping columns/tables.
2. **Column rollback** — `ALTER TABLE ... DROP COLUMN IF EXISTS` only if no data depends on it.
3. **Table rollback** — `DROP TABLE IF EXISTS` only in staging; avoid in production unless table is empty and unused.
4. **Full restore** — restore from pre-migration backup if a migration causes data corruption.

No destructive DDL is present in migrations 001–020.

---

## Stop conditions

Stop and escalate if:

- Migration ordering is ambiguous (not the case here — linear numeric order)
- Duplicate schema concepts exist (none detected)
- Destructive DDL is required (none present)
- Data backfill cannot be performed safely
- Downgrade/forward-fix strategy is missing

---

## Production readiness assessment

| Assessment | Result |
| --- | --- |
| Ordering ambiguous? | **No** — strict 001→020 |
| Destructive DDL? | **No** — all additive/idempotent |
| Duplicate concepts? | **No** |
| Safe backfill needed? | **No** — column adds with defaults |
| Blocker? | **None** for migration review |

**Migration review: PASS** (pending staging rehearsal).
