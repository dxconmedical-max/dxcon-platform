# Database Freeze — Release 2.0

## Inventory

See `backend/generated_release/DATABASE_FREEZE_REPORT.json` for table count, migrations, and ownership sample.

## Migration files

| File | Domain |
|------|--------|
| `001_business_engine_sprint1.sql` | Core business engine |
| `002_uat_critical_fixes.sql` | UAT fixes |
| `003_mdm_foundation.sql` | Master data |
| `004_partner_foundation.sql` | Partners |
| `005_reception_workspace.sql` | Reception |
| `006_lab_workspace.sql` | Laboratory |
| `007_reporting_engine.sql` | Reporting |
| `008_portal.sql` | Portals |
| `009_executive_platform.sql` | Executive |
| `010_operations_center.sql` | Operations center |
| `011_integration_platform.sql` | Integration (Epic 3.5) |

## Rules

1. No table renaming without compatibility migration.
2. No destructive column removal in Release 2.x.
3. Tenant-owned business tables must include `organization_id` (or equivalent).
4. Released reports and signed results are **immutable**.
5. All migrations must be backward compatible (`CREATE IF NOT EXISTS`, additive columns).
6. Destructive SQL (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`) is blocked by architecture guardrails.

## Immutable records

- Released diagnostic reports
- Signed/approved results after release
- Audit log entries
- Payment reconciliation records after settlement

## Soft delete

Where soft delete is used, records retain `deleted_at` / `is_active` and remain queryable for audit. Hard delete is prohibited for clinical and financial records.

## Verification

```bash
python backend/scripts/verify_tenant_model_coverage.py
```
