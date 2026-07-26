# Barcode Module — Release 2 Step 5

**Status:** Implemented  
**Scope:** Barcode service, page, printing, sample/order/collection labels, thermal labels, printer abstraction, tests  
**Out of scope:** QR product milestone, hardware ESC/POS drivers  

---

## Service

`backend/app/reception_workspace/barcode_engine.py`

Reuses `generate_barcodes()` for stable paid-order identifiers (no new IDs on reprint).

| Label type | Source |
|------------|--------|
| Order | `order_barcode` / `BC-{order_code}` |
| Sample | Per order item `BC-SMP-{test}-{order}` |
| Collection | `BizCollection.barcode_value` when collection exists |
| Patient | `BC-PAT-{patient_code}` |

---

## Printer abstraction

`backend/app/reception_workspace/printers.py`

| Adapter | Media | Role |
|---------|-------|------|
| `browser` | `label` | CSS label sheets → browser print dialog |
| `thermal` | `thermal_label` | 80mm HTML + plain-text for ESC/POS bridges |

Adapters return `PrintJob` payloads; they do not talk to USB/network printers directly.

---

## APIs (`/api/v1/reception/workspace`)

| Method | Path |
|--------|------|
| GET | `/orders/:ref/barcode` — stable codes (add `?labels=1` for label bundle) |
| GET | `/orders/:ref/barcode/labels?types=order,sample,collection,patient` |
| GET | `/orders/:ref/barcode/preview?format=standard\|thermal` |
| POST | `/orders/:ref/barcode/print` — body: `{ types, format, printer }` |
| GET | `/barcode/printers` |

Paid orders only (same gate as existing barcode generation).

---

## UI

- Page: `/app/reception/m2/barcode` (`?order=ORD-…`)
- Component: `BarcodeWorkbench`
- Module: `apps/web/src/modules/reception-m2/barcode/`
- Client: `@/lib/api/reception` barcode helpers

---

## Thermal support

- 80mm `@page` CSS label sheets
- `thermal_text` plain blocks for bridge/copy-paste
- Prefer browser print with thermal CSS (no proprietary binary ESC in API)

## Audit

- Existing: `barcode_generated` / `barcode_printed` via `generate_barcodes`
- Print job: `barcode_labels_printed`

---

## Tests

`backend/tests/test_barcode_engine.py`
