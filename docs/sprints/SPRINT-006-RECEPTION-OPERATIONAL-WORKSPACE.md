# Sprint 006 — Reception Operational Workspace

## Goal

Production-ready front-desk workspace at `/app/reception` integrating patient search, registration, orders, payment, barcodes, queue, and audit.

## Modules

1. **Workspace UI** — 3-column dashboard with KPIs, search, queue, quick actions
2. **Patient Search** — Fast unified search (code, name, phone, national ID, QR)
3. **Registration** — Via business engine with duplicate detection
4. **Orders & Payment** — Full workflow through business engine
5. **Barcodes & Request Form** — Post-payment labels and printable forms
6. **Collection Queue** — Auto collection job after payment
7. **API** — `/api/v1/reception/workspace/*` with session/JWT auth
8. **Migration** — `005_reception_workspace.sql` (queue order/invoice/workflow columns)

## Verify

```bash
python3 -m compileall backend/app backend/scripts backend/tests
python3 -m unittest discover -s backend/tests -v -k reception_workspace
python3 backend/scripts/verify_reception_workspace.py
```

## Reports

- `generated_release/RECEPTION_WORKSPACE_REPORT.json`
- `generated_release/PAYMENT_REPORT.json`
- `generated_release/QUEUE_REPORT.json`
