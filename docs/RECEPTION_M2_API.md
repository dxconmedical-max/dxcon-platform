# Reception Milestone 2 — API Contracts

**Prefix:** `/api/v1/reception/workspace`  
**Auth:** Bearer JWT (Reception / Admin roles) · optional `X-Organization-ID`  
**Client:** `@/lib/api/reception` (canonical)  
**Module facades:** `apps/web/src/modules/reception-m2/*/service.ts`  
**Backend changes in this foundation:** **None**

---

## 1. Contract ownership

| Domain | HTTP | Client function | M2 facade |
|--------|------|-----------------|-----------|
| Order context (shared) | `GET /orders/:ref` | `fetchReceptionOrder` | payment / receipt |
| Payment | `POST /orders/:ref/payment` | `collectReceptionPayment` | `payment/service` |
| Receipt | *(none)* — from payment / order payload | — | `receipt/service` view map |
| Barcode | `GET /orders/:ref/barcode` | `fetchReceptionBarcodes` | `barcode/service` |
| Request form (related) | `GET /orders/:ref/request-form` | `fetchReceptionRequestForm` | barcode (optional) |
| QR | `GET /orders/:ref/qr`, `POST /qr/verify` | `fetchReceptionQrBundle` / `verifyReceptionQr` | `qr/service` |
| Lab Queue | `GET /lab-queue`, enqueue/advance/priority | `fetchLabQueueDashboard` / … | `lab-queue/service` |
| Sample Queue | `GET /sample-queue`, track/history/advance | `fetchSampleQueueDashboard` / … | `sample-queue/service` |

---

## 2. Payment

### `POST /orders/:ref/payment`

| | |
|--|--|
| **Headers** | `Authorization`, `Idempotency-Key` |
| **Body** | `payment_method`, `amount`, `receipt_number?`, `idempotency_key` |
| **Methods** | `cash` \| `transfer` \| `qr` \| `pos` \| `corporate` \| `insurance` |
| **Response** | `{ payment, invoice, order_status, payment_summary, idempotent_replay? }` |
| **Timeout** | `RECEPTION_PAYMENT_TIMEOUT_MS` (30s) |

`payment_summary`: `order_total`, `paid_amount`, `outstanding_amount`, `status`, method flags.

**Foundation note:** Facade exports the client only — **no UI collect logic yet**.

---

## 3. Receipt

No dedicated receipt endpoint on the R1 workspace contract.

| Source | Fields |
|--------|--------|
| `payment` on payment result / order detail | `receipt_number`, `payment_method`, `amount`, `paid_at`, `created_by` |
| Order | `order_code` |

M2 `ReceiptViewModel` is a pure front-end view map — not a new API.

---

## 4. Barcode

### `GET /orders/:ref/barcode`

Returns `ReceptionBarcodes`:

- `order_barcode`, `patient_barcode`, `patient_qr`
- `sample_barcodes[]` (`test_code`, `barcode`, `sample_type`, …)
- `collection_barcode?`, `reprint?`, `generated_at?`

### Related

`GET /orders/:ref/request-form` — HTML requisition; may embed barcode payload.

---

## 5. QR

### `GET /orders/:ref/qr`

Query: `kinds` (comma: `payment,vnpay,static,dynamic,sample,tracking`), `amount`, `images`, `preview`.

Returns `qrs[]` with `payload`, `image_data_url`, `meta`.

### `POST /qr/verify`

Body: `{ payload, order_ref? }` → `{ valid, kind, reason, fields }`.

### Legacy

| Source | Value |
|--------|--------|
| Barcode payload | `patient_qr` (`dxcon:patient:…`) |
| Validation helper | `isValidPatientQr` |

See `docs/QR_MODULE.md`.

---

## 6. Lab Queue

### Dashboard

| Method | Path |
|--------|------|
| GET | `/lab-queue` |
| GET | `/lab-queue/stats` |
| GET | `/lab-queue/refresh?version=` |
| POST | `/lab-queue/orders/:ref/enqueue` |
| POST | `/lab-queue/orders/:ref/advance` |
| POST | `/lab-queue/orders/:ref/priority` |

Stages: `waiting` → `processing` → `completed` → `verified`.  
Priorities: `urgent` · `high` · `routine` · `low`.

See `docs/LAB_QUEUE_MODULE.md`.

### Handoff (enqueue path)

### `POST /orders/:ref/lab-handoff`

Body (defaults allowed by client): `laboratory_name`, `laboratory_id?`, `collector_name`, `pickup_address`.

Returns `lab_queue` row when entered.

### `GET /orders/:ref/lab-handoff`

Status read / reopen.

Response `ReceptionLabHandoff`: `order_code`, `order_status`, `collection`, `queue_entry`, `queue_reference`, `laboratory`, `accepted_at`, `barcodes?`, `handed_off?`, `idempotent_replay?`, `lab_queue?`.

---

## 7. Sample Queue

### Dashboard / tracking

| Method | Path |
|--------|------|
| GET | `/sample-queue` |
| GET | `/sample-queue/refresh?version=` |
| POST | `/sample-queue/orders/:ref/enqueue` |
| POST | `/sample-queue/orders/:ref/advance` |
| GET | `/sample-queue/orders/:ref/track` |
| GET | `/sample-queue/orders/:ref/history` |
| POST | `/sample-queue/orders/:ref/tracking` |

Stages: `collected` → `transport` → `received` → `sorting` → `laboratory` → `completed`.

See `docs/SAMPLE_QUEUE_MODULE.md`.

Legacy handoff mapping (`collection` / `queue_entry`) remains available for status panels.

---

## 8. Error / idempotency notes

| Concern | Contract |
|---------|----------|
| Payment replay | `Idempotency-Key` + `idempotent_replay` |
| Handoff replay | `idempotent_replay` on handoff payload |
| Auth | 401 / 403 via existing `ApiError` |
| Missing order | 404 on order/barcode/handoff reads |

---

## 9. Non-goals

- New Flask routes  
- Alembic / SQL migrations  
- Changing payment validation rules  
- Mock payment success in production  

See `docs/RECEPTION_M2_ARCHITECTURE.md`.
