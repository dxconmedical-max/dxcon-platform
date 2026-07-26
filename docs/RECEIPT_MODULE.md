# Receipt Module — Release 2 Step 4

**Status:** Implemented  
**Scope:** Receipt model, service, page, preview, print, thermal, PDF, re-print, cancel, audit  
**Out of scope:** Barcode / QR product work  

---

## Model

`BizReceipt` (`biz_receipts`) — one receipt per `BizPayment`

| Field | Notes |
|-------|--------|
| `receipt_code` | Unique; usually mirrors payment `receipt_number` |
| `payment_id` | Unique FK |
| `status` | `issued` · `reprinted` · `cancelled` |
| `print_count` | Incremented on print/reprint |
| `html_snapshot` / `thermal_payload` | Preview payloads |
| `pdf_path` | Persisted PDF artifact |
| cancel fields | `cancelled_at`, `cancelled_by`, `cancel_reason` |

Migration: `backend/migrations/017_reception_receipts.sql`

---

## Service

`backend/app/reception_workspace/receipt_engine.py`

- Auto-issue on payment collect (`ensure_receipt_for_payment`)
- Preview (standard / thermal HTML + thermal text)
- Print / re-print (audit + print_count)
- PDF (ReportLab via `receipt_pdf.py`)
- Cancel (blocks further print/PDF)

---

## APIs (`/api/v1/reception/workspace`)

| Method | Path |
|--------|------|
| GET | `/orders/:ref/receipts` |
| GET | `/receipts/:ref` |
| GET | `/receipts/:ref/preview?format=standard\|thermal` |
| POST | `/receipts/:ref/print` |
| POST | `/receipts/:ref/reprint` |
| GET | `/receipts/:ref/pdf` |
| POST | `/receipts/:ref/cancel` |
| POST | `/payments/:ref/receipt` |

---

## UI

- Page: `/app/reception/m2/receipt`
- Component: `ReceiptWorkbench` (preview, print, thermal, PDF link, reprint, cancel)
- Client: `@/lib/api/reception` receipt helpers (no duplicated payment logic)

---

## Tests

`backend/tests/test_receipt_engine.py`

---

## Thermal support

- 80mm HTML (`@page` + monospace layout)
- Plain-text `thermal_payload` for ESC/POS-friendly drivers / copy-paste
- Prefer browser print dialog with thermal CSS (no proprietary binary ESC in API)

## Audit

Actions: `reception.receipt_issued`, `receipt_printed`, `receipt_reprinted`, `receipt_pdf_generated`, `receipt_cancelled`
