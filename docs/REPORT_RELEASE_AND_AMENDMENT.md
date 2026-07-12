# Report Release and Amendment

## Release prerequisites

- Technician validation complete
- Doctor approval complete (`clinical_reports.report_status = approved`)
- Report PDF/hash generated
- Signature recorded (`report_digital_signatures`)
- No unresolved critical alerts
- Explicit `POST /api/v1/clinical/release/{order_ref}`

## Amendment

Use reporting engine amendment API. New `report_version`; prior PDF retained. Amended notice on new PDF.

## Revocation

Set report status `revoked`; verification endpoint shows revoked status. Never delete released PDFs.
