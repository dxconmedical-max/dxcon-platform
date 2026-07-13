# Migrations 016–020 — Staging Runbook

**Release:** 8.1 · **Target:** Staging database only
**Do not run on production until staging UAT passes.**

---

## Pre-migration

- [ ] Staging Postgres provisioned (separate from production)
- [ ] Staging DB backup/snapshot taken
- [ ] Migrations 001–015 already applied (or full chain from empty staging DB)
- [ ] Record current schema inventory:
  ```sql
  SELECT table_name FROM information_schema.tables
    WHERE table_schema='public' ORDER BY 1;
  ```

---

## Apply (staging only)

```bash
export DATABASE_URL="<staging-postgres-url>"

for migration in \
  backend/migrations/016_lims_core.sql \
  backend/migrations/017_iot_logistics.sql \
  backend/migrations/018_analyzer_integration.sql \
  backend/migrations/019_clinical_workflow.sql \
  backend/migrations/020_patient_commerce.sql
do
  echo "Applying $migration ..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
```

For **fresh staging DB**, apply 001–020 in order (see `docs/PRODUCTION_MIGRATION_RUNBOOK.md`).

---

## Post-migration verification

```sql
-- 016 LIMS
SELECT COUNT(*) AS specimens_table FROM information_schema.tables WHERE table_name = 'specimens';

-- 017 IoT
SELECT column_name FROM information_schema.columns
  WHERE table_name = 'iot_devices' AND column_name = 'organization_id';

-- 018 Analyzer
SELECT column_name FROM information_schema.columns
  WHERE table_name = 'lab_analyzers' AND column_name = 'vendor';

-- 019 Clinical
SELECT column_name FROM information_schema.columns
  WHERE table_name = 'biz_result_items' AND column_name = 'result_status';

-- 020 Commerce
SELECT COUNT(*) AS slot_holds_table FROM information_schema.tables WHERE table_name = 'mp_slot_holds';
```

---

## Application verification

1. Deploy backend to staging with `APP_ENV=staging`
2. Confirm boot: `GET https://api-staging.dxcon.com.vn/api/v1/system/health` → 200
3. Seed pilot accounts (see `docs/STAGING_UAT_EXECUTION.md`)
4. Run smoke tests with staging URLs
5. Execute UAT-01 through UAT-16

---

## Rollback

All migrations are additive (`IF NOT EXISTS`). Rollback strategy:

1. **Forward-fix** preferred
2. Restore from pre-migration snapshot if schema corruption occurs
3. Do not `DROP TABLE` in staging without confirming no dependent pilot data

---

## Stop conditions

Stop and escalate if:

- Any migration fails with `ON_ERROR_STOP`
- Verification queries return 0 when tables expected
- Application boot fails after migration
