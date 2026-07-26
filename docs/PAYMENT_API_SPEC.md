# Payment API Spec — Reception M2 Step 2

**Canonical stack:** Reception Workspace + Business Engine  
**Base:** `/api/v1/reception/workspace`  
**Client:** `apps/web/src/lib/api/reception.ts`  
**Rule:** Document **existing** contracts only. Do not invent endpoints.  
**No implementation in this step.**

---

## 1. Authorization (all endpoints below)

| Aspect | Behavior |
|--------|----------|
| Auth | JWT Bearer or session (workspace decorators) |
| Roles | `RECEPTION`, `ADMIN`, `SUPER_ADMIN`, `SYSTEM_ADMIN` |
| Write | `@reception_api_write` — create order, collect payment |
| Read | `@reception_api_read` — get order, payment-report |
| Permission string | `payments.collect` exists in catalog; routes gate by **role**, not string check |

**Not Reception M2:** Unauthenticated `/api/v1/billing` and `/api/v1/payments` — out of scope for cash-desk; security debt tracked in gap analysis.

---

## 2. POST Create order (pricing + invoice)

### `POST /orders`

| | |
|--|--|
| **Auth** | write |
| **Idempotency** | None on this route |
| **Payload** | |

```json
{
  "patient_code": "P-…",
  "test_catalog_ids": ["uuid", "…"],
  "discount": 0,
  "note": "optional",
  "queue_entry_id": "optional"
}
```

Alias accepted: `tests` for catalog ids.

| **Validation** | ≥1 test; valid patient; discount coerced float |
| **Response 201** | |

```json
{
  "success": true,
  "data": {
    "order": { },
    "invoice": {
      "id": "…",
      "invoice_no": "INV-…",
      "order_id": "…",
      "amount": 150000,
      "status": "unpaid"
    },
    "pricing": {
      "subtotal": 150000,
      "discount": 0,
      "total": 150000
    }
  }
}
```

| **Errors** | `400` `{ success:false, error }` — `ReceptionWorkspaceError` / `BusinessEngineError` |
| **Side effects** | Order → `payment_pending`; invoice created; queue `PAYMENT_PENDING` when linked |

---

## 3. GET Order with payment context

### `GET /orders/<order_ref>`

`order_ref` = `order_code` or order `id`.

| **Auth** | read |
| **Response 200** | |

```json
{
  "success": true,
  "data": {
    "order": { },
    "pricing": {
      "subtotal": 150000,
      "discount": 0,
      "total": 150000,
      "tax": null
    },
    "payment_summary": {
      "order_total": 150000,
      "paid_amount": 0,
      "outstanding_amount": 150000,
      "discount": 0,
      "subtotal": 150000,
      "tax": null,
      "status": "unpaid",
      "payment_methods_supported": ["cash","transfer","qr","pos","corporate","insurance"],
      "partial_payments_supported": false
    },
    "payment": null,
    "invoice": { "status": "unpaid", "amount": 150000 }
  }
}
```

| **Errors** | `404` order not found |

---

## 4. POST Collect payment

### `POST /orders/<order_ref>/payment`

| **Auth** | write |
| **Idempotency** | Body `idempotency_key` **or** header `Idempotency-Key` / `Idempotency-key`. Lookup: `BizPayment` where `order_id` + `receipt_number == key`. |
| **Payload** | |

```json
{
  "payment_method": "cash",
  "amount": 150000,
  "receipt_number": "optional-or-same-as-key",
  "idempotency_key": "uuid"
}
```

Defaults: `payment_method` → `cash`; `amount` → full outstanding if omitted; `receipt_number` → key or generated `RCT-…`.

| **Validation** | |
|----------------|--|
| Method ∈ allow-list | else 400 |
| amount > 0 | else 400 |
| amount ≤ outstanding | else 400 overpayment |
| amount ≥ outstanding (within 0.009) | Full pay → paid |
| amount < outstanding | **Partial allowed** → status `partial`; order stays `payment_pending` |
| Order exists | else 400/engine error |

| **Response 200** | |

```json
{
  "success": true,
  "data": {
    "payment": {
      "id": "…",
      "invoice_id": "…",
      "order_id": "…",
      "payment_method": "cash",
      "receipt_number": "…",
      "amount": 150000,
      "paid_at": "ISO-8601",
      "created_by": "actor"
    },
    "invoice": { "status": "paid", "amount": 150000 },
    "order_status": "paid",
    "payment_summary": {
      "status": "paid",
      "outstanding_amount": 0,
      "partial_payments_supported": false
    },
    "idempotent_replay": false
  }
}
```

Replay: same shape with `idempotent_replay: true`.

| **Errors** | `400` `{ success:false, error: "<message>" }` |
| **DELETE / PUT** | **Not present** for reception payments |

---

## 5. GET Payment report

### `GET /payment-report`

| **Auth** | read |
| **Response** | `{ success, data: payment_report() }` — methods, statuses, payments today, pending orders (service-defined) |

---

## 6. Downstream (post-paid) — referenced, not payment APIs

| Method | Path | Note |
|--------|------|------|
| GET | `/orders/<ref>/barcode` | Requires paid |
| GET | `/orders/<ref>/request-form` | Requires paid |
| POST/GET | `/orders/<ref>/lab-handoff` | Requires paid |

---

## 7. Methods matrix (GET/POST/PUT/DELETE)

| Resource | GET | POST | PUT | DELETE |
|----------|-----|------|-----|--------|
| Orders | ✓ detail | ✓ create | ✗ | ✗ |
| Payment on order | ✓ history (`/payments`) + embedded on GET order | ✓ collect (full/partial) | ✗ | ✗ |
| Payment report | ✓ | ✗ | ✗ | ✗ |
| Receipt entity | ✗ | ✗ | ✗ | ✗ |
| Refund (biz) | ✗ | ✗ | ✗ | ✗ |

---

## 8. Error codes (actual)

Reception routes return **string `error` messages**, not structured machine codes (except some handoff paths that set `code` in `ApiError` on the **frontend** client). Backend payment collect:

| HTTP | Typical `error` text |
|------|----------------------|
| 400 | `Invalid payment method: …` |
| 400 | `Payment amount must be greater than zero` |
| 400 | `Overpayment is not allowed (outstanding=…)` |
| 400 | `Partial payments are not supported. Collect the full outstanding amount.` |
| 400/404 | `Order not found` |
| 401/403 | Auth decorator failures |

**Recommended future (gap):** stable `code` field e.g. `INVALID_METHOD`, `OVERPAYMENT`, `PARTIAL_NOT_SUPPORTED`, `ORDER_NOT_PAYABLE`.

---

## 9. Frontend binding (existing)

| Function | Path |
|----------|------|
| `createReceptionOrder` | POST `/orders` |
| `fetchReceptionOrder` | GET `/orders/:ref` |
| `collectReceptionPayment` | POST `/orders/:ref/payment` + `Idempotency-Key` |

Constants: `RECEPTION_PAYMENT_METHODS`, `RECEPTION_PAYMENT_TIMEOUT_MS = 30000`.

---

## 10. Out-of-scope APIs (exist but not Reception cash desk)

Do **not** call these for M2 Payment UI without architecture decision:

- `POST /api/v1/billing/invoices/<id>/mark-paid`
- `POST /api/v1/payments/create`
- `POST /api/v1/billing/refunds`
- Marketplace `POST /api/v1/marketplace/v2/payments/qr`
