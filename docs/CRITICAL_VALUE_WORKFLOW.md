# Critical Value Workflow

Configurable policies in `critical_value_policies` (per test/analyte, thresholds, SLA).

## Detection

On technician validation, values compared to active policies → `CriticalResultAlert` created.

## Acknowledgement

1. Technician acknowledges alert (`POST /api/v1/clinical/critical/{id}/acknowledge`)
2. Doctor/authorized clinician notified per policy
3. Communication method and timestamp recorded in `critical_value_acknowledgements`
4. Unresolved alerts block governed release

No silent dismissal. Escalation schedule stored in policy JSON for future automation.
