# SPRINT-003 — Business Stabilization (Post-UAT)

## Sprint ID

`SPRINT-003`

## Title

Business Workflow Stabilization After UAT

## Status

`IN_PROGRESS`

## Dates

- **Start:** 2026-07-04
- **Target end:** 2026-07-12

---

## Goal

Close Critical and High bugs from UAT roles 2–5 (Collector, Lab, Doctor, Patient) so core diagnostic workflow runs end-to-end on PostgreSQL with audit trails.

## Business Value

Release 1.0 pilot cannot start until real users can complete orders without workarounds. UAT exposed gaps in audit logging, QC gates, barcodes, and patient portal data.

## Scope

- Safe `write_audit` when `audit_logs.request_id` column missing (session introspection)
- Migration `002_uat_critical_fixes.sql` — `audit_logs.request_id`, `biz_orders.barcode_value`
- Business engine: `accept_collection`, `update_chain_of_custody`, `complete_qc` (split from `enter_results`)
- Barcode on payment; `get_patient_portal_data`; PostgreSQL patient insert fix
- Business UI routes: accept, in-transit, custody, complete-qc, print-request
- Launch UI: patient search, edit form, order workflow actions, real portal data
- UAT scripts: collector, lab, doctor, patient + `uat_lib.py`
- UAT reports in `backend/generated_release/`
- Fix duplicate route `/api/v1/population-health/dashboard` (if still open)
- `ops_maintenance_windows` table for health DEGRADED in tests

## Out of Scope

- Payment gateway live integration
- PDF report engine
- Mobile collector app
- Medium/Low UAT items (backlog only)

## Deliverables

- [x] `backend/app/core/audit.py` — safe audit write
- [x] `backend/app/infrastructure/schema_introspection.py` — session connection fix
- [x] `backend/migrations/002_uat_critical_fixes.sql`
- [x] `backend/app/business_engine/service.py` — workflow gaps
- [x] `backend/app/web/business_ui.py`, `launch_ui_modules.py`
- [x] `backend/scripts/uat_lib.py`, `verify_uat_*.py` (4 roles)
- [ ] `UAT_BUG_SUMMARY.json`, `BUG_BACKLOG.md`, `UAT_FINAL_REPORT.json`
- [ ] Full unit test suite green (13 known failures pre-governance)
- [ ] Commit: `UAT 2-5 - Workflow Validation and Critical Fixes`

## Data Impact

| Area | Change | Migration |
|------|--------|-----------|
| `audit_logs` | `request_id` column | `002_uat_critical_fixes.sql` |
| `biz_orders` | `barcode_value` column | `002_uat_critical_fixes.sql` |

## API Impact

| Endpoint | Change |
|----------|--------|
| Business workflow routes | New web POST handlers for collection/custody/QC |
| Population health | Remove duplicate dashboard route |

## UI Impact

| Route | Change |
|-------|--------|
| `/app/collector`, `/app/lab` | Workflow action buttons |
| `/app/patient` | Real order/report/invoice data |
| `/app/reception` | Patient search and edit |

## Tests

```bash
python3 backend/scripts/verify_uat_collector.py
python3 backend/scripts/verify_uat_lab.py
python3 backend/scripts/verify_uat_doctor.py
python3 backend/scripts/verify_uat_patient.py
python3 backend/scripts/verify_business_engine.py
python3 backend/scripts/generate_uat_final_report.py
```

## Verification

**UAT (PostgreSQL):** Collector 10/10, Lab 9/9, Doctor 8/8, Patient 7/7 — PASS.

**Pending:** Final reports, full unittest suite, commit and push.

## Definition of Done

- [x] All four role UAT scripts PASS on PostgreSQL
- [ ] UAT final report generated
- [ ] Critical/High bugs fixed; Medium/Low in backlog
- [ ] `verify_business_engine.py` PASS
- [ ] Sprint status DONE
- [ ] Committed and pushed to `main`

## Commit Message

```
UAT 2-5 - Workflow Validation and Critical Fixes
```

## Notes

- Reception UAT script exists (`verify_uat_reception.py`) — include in final report.
- Enterprise hardening failure: bare `except` in `launch_ui_data.py` — fix in this sprint or 1.1.
- Monitoring tests fail without `ops_maintenance_windows` — additive migration or test fixture.
