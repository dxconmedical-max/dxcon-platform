# Clinical Workflow State Machines — Release 2.0

## Order lifecycle (frozen target)

```
CREATED → CONFIRMED → PAYMENT_PENDING → PAID → COLLECTION_SCHEDULED →
COLLECTOR_ASSIGNED → COLLECTION_IN_PROGRESS → COLLECTED → IN_TRANSIT →
LAB_RECEIVED → TESTING → QC_PENDING → VALIDATION_PENDING → REPORT_PENDING →
RELEASED → CLOSED
```

Terminal: `CANCELLED`

**Implementation:** `MEDICAL_ORDER_*` in `app/core/statuses.py` with `MEDICAL_ORDER_TRANSITIONS`. Some state names differ (e.g. `BOOKED` vs `CREATED`) — mapping documented in freeze report.

## Sample lifecycle (frozen)

```
CREATED → LABELLED → COLLECTED → PACKED → IN_TRANSIT → RECEIVED →
ACCEPTED → TESTING → COMPLETED → DISPOSED
```

Terminal: `REJECTED`

## Result lifecycle (frozen)

```
DRAFT → ENTERED → QC_PENDING → QC_PASSED → VALIDATION_REQUIRED →
PENDING_REVIEW → APPROVED → RELEASED
```

Terminal: `REJECTED` | Amendment: `AMENDED` (new version)

## Rules

1. Invalid transitions return **409 INVALID_STATE_TRANSITION**.
2. Every transition is audited.
3. Released clinical records are immutable.
4. Amendments create new version; original preserved.
5. No Epic may bypass approval gates or auto-release imported results.

## Verification

```bash
python backend/scripts/verify_clinical_state_machines.py
```

`CLINICAL_WORKFLOW_FREEZE_REPORT.json`
