# Staging Migration Execution — 016–020 (Release 9.0)

**Database:** staging PostgreSQL only.  
**Do not** set `DATABASE_URL` to production.

Ordering is **not ambiguous**. All files are additive (`IF NOT EXISTS`). No destructive DDL in 016–020.

---

## Prerequisites

1. Staging Postgres provisioned and empty or known baseline  
2. Backup / snapshot created  
3. Migrations **001–015** already applied (or apply full `0*.sql` chain on a fresh DB)  
4. Confirm:

```bash
echo "$DATABASE_URL" | grep -vi production | grep -qi staging || echo "VERIFY URL IS STAGING"
```

---

## Inventory

| Order | File | Dependency | Changes | Type | Lock risk | Backfill |
|---|---|---|---|---|---|---|
| 16 | `016_lims_core.sql` | Lab foundation tables | specimens, containers, accessions, barcodes | CREATE IF NOT EXISTS | Medium | None |
| 17 | `017_iot_logistics.sql` | `iot_devices` exists | IoT columns + cold-chain tables | ALTER/CREATE IF NOT EXISTS | Low | None |
| 18 | `018_analyzer_integration.sql` | `lab_analyzers` exists | Analyzer columns + integration tables | ALTER/CREATE IF NOT EXISTS | Low | None |
| 19 | `019_clinical_workflow.sql` | `biz_result_items` exists | Result governance columns + transition table | ALTER/CREATE IF NOT EXISTS | Low | None |
| 20 | `020_patient_commerce.sql` | `mp_providers` / marketplace | Slot holds + commerce columns | ALTER/CREATE IF NOT EXISTS | Low | None |

---

## Execution

```bash
export DATABASE_URL="<STAGING_POSTGRESQL_URL>"

# Schema inventory before
psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1;"

# Apply 016–020
bash backend/scripts/apply_staging_migrations_016_020.sh

# Or manually:
for f in \
  backend/migrations/016_lims_core.sql \
  backend/migrations/017_iot_logistics.sql \
  backend/migrations/018_analyzer_integration.sql \
  backend/migrations/019_clinical_workflow.sql \
  backend/migrations/020_patient_commerce.sql
do
  echo "=== $f ==="
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

---

## Pre-check SQL

```sql
-- 017 needs iot_devices (from earlier migrations)
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iot_devices';
-- 018 needs lab_analyzers
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'lab_analyzers';
-- 019 needs biz_result_items
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'biz_result_items';
-- 020 needs mp_providers
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mp_providers';
```

## Post-check SQL

```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'specimens';
SELECT column_name FROM information_schema.columns WHERE table_name='iot_devices' AND column_name='organization_id';
SELECT column_name FROM information_schema.columns WHERE table_name='lab_analyzers' AND column_name='vendor';
SELECT column_name FROM information_schema.columns WHERE table_name='biz_result_items' AND column_name='result_status';
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mp_slot_holds';
```

---

## After migration

1. Boot staging API → `/api/v1/system/health` = 200  
2. Run `python backend/scripts/bootstrap_staging_pilot.py --dry-run` then `--apply`  
3. Run staging smoke tests  
4. Run UAT package  

## Forward-fix / rollback

- Forward-fix preferred (additive schema)  
- Rollback limitation: no automated down migrations; restore snapshot if needed  

## Stop conditions

Stop if any `psql` exits non-zero, pre-checks return 0 for required tables, or application fails to boot.
