# Billing Status (Pilot)

## Supported

- Standard invoices and payments for orders (Business Engine)
- Patient invoice visibility in patient portal (basic)

## Placeholders (Release 2.0)

- Corporate billing workflows
- Insurance billing / claims integration
- Commission engine (doctor commission)

## Pilot behavior

- Show **“Coming in Release 2.0”** where corporate/insurance workflows are referenced.
- Do not expose unsafe payment actions if not fully implemented.

## Generated status report

Run:

```bash
python backend/scripts/verify_pilot_blockers.py
```

Outputs:
- `backend/generated_release/BILLING_STATUS_REPORT.json`

