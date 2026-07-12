# Clinical Result Workflow

Release 8.0 Sprint 6 — canonical governed path for internal pilot.

## Flow

1. Order confirmed and specimen collected (LIMS + business engine)
2. Analyzer ingests **preliminary** result (Sprint 5) — never auto-released
3. Technician promotes preliminary → `biz_result_item` with `original_value` preserved
4. Technician validates → `TECHNICIAN_VALIDATED`; critical policies evaluated
5. Doctor reviews via reporting engine → approves and signs
6. Explicit **governed release** (`POST /api/v1/clinical/release/{order_ref}`)
7. Verification token issued; patient/clinic portals show released PDF only

## Transition engine

`clinical_governance/workflow.py` validates transitions from `CLINICAL_RESULT_TRANSITIONS` and `CLINICAL_REPORT_TRANSITIONS`. Immutable history in `clinical_workflow_transitions`.

## Safety

- No direct jump to `RELEASED` on results
- No automatic doctor approval
- Amendments create new report version; prior PDF retained
