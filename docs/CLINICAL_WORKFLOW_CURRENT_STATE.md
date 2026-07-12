# Clinical Workflow — Current State

Release 8.0 Sprint 6 discovery snapshot.

## Canonical pilot path

Orders, results, and reports for internal pilot use the **business engine** stack:

- `biz_orders` / `biz_order_items`
- `biz_results` / `biz_result_items` (extended in migration `019_clinical_workflow.sql`)
- `clinical_reports` via `reporting_engine`
- `analyzer_preliminary_results` (Sprint 5) bridged by `clinical_governance.promote_preliminary_to_result`

## Parallel stores (not pilot-canonical)

| Store | Purpose | Sprint 6 action |
|-------|---------|-----------------|
| `test_results` | Legacy order module | Do not duplicate |
| `lab_results` | Result gateway / medical orders | Retain; not primary pilot path |
| `biz_results` | Reporting + governance | **Primary** |

## Lifecycle fields

### Order (clinical constants in `statuses.py`)

`DRAFT` → `PENDING_CONFIRMATION` → `CONFIRMED` → collection states → `IN_LAB` → `PROCESSING` → `RESULTS_PENDING_REVIEW` → `PARTIALLY_COMPLETED` / `COMPLETED` / `CANCELLED`

Biz orders continue using business-engine statuses; clinical constants document the target unified model.

### Specimen (Sprint 3 LIMS)

Reuse `LIMS_SPECIMEN_*` states from Sprint 3 — no duplicate specimen model.

### Result

`PENDING` → `PRELIMINARY` → `TECHNICIAN_REVIEW` → `TECHNICIAN_VALIDATED` → `DOCTOR_REVIEW` → `APPROVED` → `RELEASED` (+ `AMENDED`, `WITHDRAWN`, `REJECTED`)

Transitions enforced in `clinical_governance/workflow.py`.

### Report

`DRAFT` → `PENDING_APPROVAL` → `APPROVED` → `RELEASED` (+ `AMENDED`, `REVOKED`)

Reporting engine uses lowercase aliases (`approved`, `released`) — governed release checks both.

## APIs

| Area | Prefix | Notes |
|------|--------|-------|
| Reporting | `/api/v1/reporting` | Doctor review, approve, release |
| Clinical governance | `/api/v1/clinical` | Technician queue, validate, governed release |
| Verification | `/api/v1/verify-report/{token}` | Public authenticity only |

## Safety rules (pilot)

- No automatic final clinical release
- No skip of technician validation
- Original analyzer value preserved on `biz_result_items.original_value`
- Released PDF versions immutable; amendments create new version
