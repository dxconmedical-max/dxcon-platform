# Release 9.0 — Migration Execution Plan (016–020)

**Source:** repository files under `backend/migrations/`  
**Order derived from numeric filenames in the repository (not assumed).**  
**Do not execute on production automatically.**

---

## Exact order

| Order | File |
|---|---|
| 1 | `backend/migrations/016_lims_core.sql` |
| 2 | `backend/migrations/017_iot_logistics.sql` |
| 3 | `backend/migrations/018_analyzer_integration.sql` |
| 4 | `backend/migrations/019_clinical_workflow.sql` |
| 5 | `backend/migrations/020_patient_commerce.sql` |

Prerequisite: migrations `001`–`015` already applied (or apply full chain on a fresh staging DB).

---

## Per-migration detail

### 016 — `016_lims_core.sql`

| Field | Value |
|---|---|
| Dependency | Lab workspace baseline (`006`+) |
| Classification | **Additive** (`CREATE TABLE IF NOT EXISTS`, indexes) |
| Objects created | `specimens`, `containers`, `barcode_logs`, `storage_locations`, `accessions`, `sample_status_history` + indexes |
| Lock risk | Medium (new tables; usually low lock contention) |
| Pre-check | `SELECT to_regclass('public.specimens');` → should be NULL before first apply |
| Post-check | `SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('specimens','accessions','containers');` → 3 |
| Rollback | Forward-fix preferred; restore staging snapshot if needed |

### 017 — `017_iot_logistics.sql`

| Field | Value |
|---|---|
| Dependency | `016` (and existing `iot_devices`) |
| Classification | **Additive** (`ALTER ... ADD COLUMN IF NOT EXISTS`, new tables) |
| Objects changed | Columns on `iot_devices` |
| Objects created | `iot_device_credentials`, `iot_device_assignments`, `iot_canonical_readings`, `iot_threshold_policies`, `iot_cold_chain_excursions`, `iot_platform_alerts`, `iot_telemetry_dead_letters`, `logistics_transport_trips` |
| Lock risk | Low–medium (ALTER TABLE ADD COLUMN on `iot_devices`) |
| Pre-check | `SELECT column_name FROM information_schema.columns WHERE table_name='iot_devices' AND column_name='organization_id';` |
| Post-check | Same query returns one row; `to_regclass('public.logistics_transport_trips')` not null |
| Rollback | Forward-fix / snapshot restore |

### 018 — `018_analyzer_integration.sql`

| Field | Value |
|---|---|
| Dependency | Lab analyzers table + preferably `016` |
| Classification | **Additive** |
| Objects changed | Columns on `lab_analyzers` |
| Objects created | `analyzer_integration_messages`, `integration_test_mappings`, `integration_quarantine`, `analyzer_worklist_items`, `analyzer_preliminary_results` |
| Lock risk | Low (`ADD COLUMN IF NOT EXISTS`) |
| Pre-check | Confirm `lab_analyzers` exists |
| Post-check | `SELECT column_name FROM information_schema.columns WHERE table_name='lab_analyzers' AND column_name='vendor';` |
| Rollback | Forward-fix / snapshot restore |

### 019 — `019_clinical_workflow.sql`

| Field | Value |
|---|---|
| Dependency | Reporting / result items (`007`+) |
| Classification | **Additive** |
| Objects changed | Columns on `biz_result_items` (governance fields) |
| Objects created | `clinical_workflow_transitions`, `critical_value_policies`, `report_verification_tokens`, `critical_value_acknowledgements` |
| Lock risk | Low |
| Pre-check | Confirm `biz_result_items` exists |
| Post-check | `result_status` column present; `report_verification_tokens` table exists |
| Rollback | Forward-fix / snapshot restore |

### 020 — `020_patient_commerce.sql`

| Field | Value |
|---|---|
| Dependency | Patient marketplace (`012`) |
| Classification | **Additive** |
| Objects changed | Columns on `mp_providers`, `mp_listings` |
| Objects created | `mp_slot_holds`, `mp_patient_addresses`, `mp_holidays`, `mp_package_items` |
| Lock risk | Low |
| Pre-check | Confirm `mp_providers` / `mp_listings` exist |
| Post-check | `to_regclass('public.mp_slot_holds')` not null; `featured` column on `mp_providers` |
| Rollback | Forward-fix / snapshot restore |

---

## Destructive DDL

**None** in 016–020. Stop the release if any future migration introduces `DROP` / destructive rewrite without a forward-fix plan.

---

## Staging execution (only)

```bash
export DATABASE_URL="<staging-postgres-url>"
# backup first
for f in \
  backend/migrations/016_lims_core.sql \
  backend/migrations/017_iot_logistics.sql \
  backend/migrations/018_analyzer_integration.sql \
  backend/migrations/019_clinical_workflow.sql \
  backend/migrations/020_patient_commerce.sql
do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

Production migrations: only after staging verification, backup, and explicit operator approval — see `docs/RELEASE_9_PRODUCTION_CUTOVER.md`.
