# LIS Integration Guide

CSV and JSON imports are operational via `/api/v1/integration/connectors/{id}/import/csv` and `/import/json`.

Imports bridge to the existing `lab_workspace/lis_service` pipeline:

`IMPORTED → VALIDATION_REQUIRED → PENDING_REVIEW → APPROVED → RELEASED`

Auto-release is disabled. Unknown external test codes are rejected to the exception queue.

HL7 ORU and REST polling are foundation-only in Epic 3.5.
