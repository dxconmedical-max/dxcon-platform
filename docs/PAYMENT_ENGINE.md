# Payment Engine — Release 2 Step 3

**Status:** Implemented (cash desk Stack A)  
**Scope:** Payment engine only — **no receipt / barcode / QR product work**  
**Reuse:** Business Engine order/invoice services; Reception workspace collect API

---

## What shipped

| Capability | Implementation |
|------------|----------------|
| Payment Engine module | `backend/app/reception_workspace/payment_engine.py` |
| Partial payments | Enabled (`partial_payments_supported: true`) |
| Methods | `cash`, `transfer` (bank transfer), `qr`, `pos`, `corporate`, `insurance` |
| Bank transfer alias | `bank_transfer` / `bank` → stored as `transfer` |
| Validation | Method allow-list, amount > 0, no overpay |
| State machine | unpaid → partial → paid (desk states) |
| History | `payments[]` on collect/get order; `GET …/orders/:ref/payments` |
| Order service reuse | `biz.record_order_payment` / `mark_order_paid` wrapper |
| No duplicated HTTP client | Web still uses `@/lib/api/reception` |

---

## Key APIs

- `POST /api/v1/reception/workspace/orders/<ref>/payment` — full or partial  
- `GET /api/v1/reception/workspace/orders/<ref>` — includes `payments` history  
- `GET /api/v1/reception/workspace/orders/<ref>/payments` — history only  

---

## Tests

- `backend/tests/test_payment_engine.py`
- Updated `backend/tests/test_reception_workspace.py` (partial path)

---

## Explicit non-scope

- Receipt print productization  
- Barcode / QR generation UX  
- Billing/gateway stack unification  
- Refunds  

See also: `docs/PAYMENT_DOMAIN_ANALYSIS.md`, `docs/PAYMENT_API_SPEC.md`.
