# Payment Domain Analysis — Reception M2 Step 2

**Role:** Principal Architect  
**Release:** 2.0 · Reception Milestone 2 · Step 2  
**Date:** 2026-07-26  
**Scope:** Analysis only — **no implementation**  
**Foundation:** Complete (`docs/RECEPTION_M2_ARCHITECTURE.md`) — not regenerated  

---

## 1. Executive summary

Reception payment for cash-desk orders is **already implemented** on the Business Engine + Reception Workspace stack (`biz_orders` / `biz_invoices` / `biz_payments`). Parallel billing and marketplace payment stacks exist but are **not** the Reception M2 cash-desk ledger.

| Area | Reception / Biz stack | Notes |
|------|----------------------|--------|
| Orders + pricing | **Present** | `subtotal − discount = total`; no VAT on total |
| Payment collect | **Present** | Full **and partial**; idempotent |
| Receipt | **Present as field** | `BizPayment.receipt_number` — no receipt table |
| Invoice | **Present** | `BizInvoice` unpaid/paid |
| Discounts | **Present (order-level)** | Float on create |
| VAT | **Not on Biz totals** | Always `tax: null` in reception summary |
| Insurance | **Method label only** | No claim/adjudication |
| Cash / Transfer / QR / POS / Corporate | **Method strings** | Validated allow-list |
| Credit (patient tender) | **Absent** | Ledger CREDIT ≠ payment method |
| Wallet | **Absent** | Labels only elsewhere |
| Refund (reception) | **Absent** | Exists on billing/gateway stacks only |
| Partial payment | **Rejected** | `partial_payments_supported: false` |

---

## 2. Part 1 — Backend audit inventory

### 2.1 Three parallel stacks (do not conflate)

| Stack | Tables | API prefix | Reception M2 role |
|-------|--------|------------|-------------------|
| **A. Reception / Business Engine** | `biz_orders`, `biz_order_items`, `biz_invoices`, `biz_payments` | `/api/v1/reception/workspace` | **Canonical for M2 Payment** |
| **B. Billing / Gateway** | `invoices`, `payment_records`, `payments`, `tax_records`, refunds, … | `/api/v1/billing`, `/api/v1/payments`, `/api/v1/invoices` | Partner/medical billing; **not** wired to BizPayment |
| **C. Marketplace** | `mp_payments`, `mp_pricing_snapshots`, … | `/api/v1/marketplace` | Patient commerce QR; separate |

### 2.2 Models (Stack A — canonical)

**Source:** `backend/app/models/biz_order.py`  
**Migration:** `backend/migrations/001_business_engine_sprint1.sql`

| Model | Table | Payment-relevant fields |
|-------|-------|-------------------------|
| `BizOrder` | `biz_orders` | `subtotal`, `discount`, `total_amount`, `status` |
| `BizOrderItem` | `biz_order_items` | `unit_price`, `quantity`, `line_total` |
| `BizInvoice` | `biz_invoices` | `invoice_no`, `order_id`, `amount`, `status` (`unpaid`/`paid`) |
| `BizPayment` | `biz_payments` | `invoice_id`, `order_id`, `payment_method`, `receipt_number` (unique), `amount`, `paid_at`, `created_by` |
| `BizWorkflowAudit` | `biz_workflow_audits` | `action`, `entity_type`, `entity_id`, statuses, `actor` |

**Queue bridge:** `ReceptionQueueEntry` — `payment_status`, `order_id`, `invoice_id`, `workflow_status` (`backend/app/models/reception_queue_entry.py`).

### 2.3 Services / repositories

| Function | File | Role |
|----------|------|------|
| `_recalc_order_totals` | `business_engine/service.py` | `total = max(subtotal − discount, 0)` — **no tax** |
| `create_order` / `add_order_item` | same | Catalog prices → line totals |
| `submit_order_for_payment` | same | → `payment_pending` |
| `create_invoice_from_order` | same | One invoice per order |
| `mark_order_paid` | same | Full invoice amount; invoice → `paid`; order → `paid` |
| `create_reception_order` | `reception_workspace/service.py` | create → submit → invoice; queue `PAYMENT_PENDING` |
| `payment_summary_for_order` | same | paid / outstanding / status; `tax: None`; `partial_payments_supported: False` |
| `collect_payment` | same | Method validation, full amount, idempotency, audit |
| `_sync_queue_after_payment` | same | Queue → `PAID` |
| `write_reception_audit` / `write_biz_audit` | audit helpers | `payment_collected` / `payment.record` |

Pricing helper (catalog/contract): `backend/app/services/pricing.py` — `get_price_for_test` (optional `ContractPrice`).

### 2.4 Reception workspace endpoints (existing — do not invent)

| Method | Path | Auth decorator | Purpose |
|--------|------|----------------|---------|
| `POST` | `/api/v1/reception/workspace/orders` | `@reception_api_write` | Create order + invoice + pricing |
| `GET` | `/api/v1/reception/workspace/orders/<order_ref>` | `@reception_api_read` | Order + pricing + payment_summary + payment + invoice |
| `POST` | `/api/v1/reception/workspace/orders/<order_ref>/payment` | `@reception_api_write` | Collect payment |
| `GET` | `/api/v1/reception/workspace/payment-report` | `@reception_api_read` | Desk payment report |
| `POST` | `…/orders/<ref>/lab-handoff` | write | Lab queue (requires paid) |
| `GET` | `…/orders/<ref>/barcode` | read | Requires paid |

Roles (workspace security): `SUPER_ADMIN`, `ADMIN`, `RECEPTION`, `SYSTEM_ADMIN`.  
Permission catalog also lists `payments.collect` for `RECEPTION` (`core/permissions.py`) — workspace gates by **role set**, not per-permission string on each route.

### 2.5 DTOs / status strings (no formal Enum class)

**Order (business_engine/statuses.py):**  
`draft` → `payment_pending` → `paid` → sampling… → lab…

**Invoice:** `unpaid` | `paid`

**Payment methods (reception):**  
`cash`, `transfer`, `qr`, `pos`, `corporate`, `insurance`

**Payment summary status (computed):**  
`unpaid` | `partial` | `paid`  
(`partial` can appear if multiple payments existed historically; **collect rejects partial amounts**)

**Report labels:** `PAYMENT_STATUSES = ("paid", "pending", "partial", "waived")` — `waived` not enforced in `collect_payment`.

### 2.6 Capability audit (requested topics)

| Topic | Existing support | Where |
|-------|------------------|-------|
| **Orders** | Yes | `BizOrder`, create/get workspace APIs |
| **Pricing** | Yes | Line items + `_recalc_order_totals`; response `pricing` |
| **Payment** | Yes | `BizPayment`, `POST …/payment` |
| **Receipt** | Number only | `receipt_number`; print is client-side |
| **Invoice** | Yes | `BizInvoice` |
| **Discounts** | Order-level float | Create payload `discount`; stored on order |
| **VAT** | Not in Biz total | `tax: null`; Stack B has `TaxRecord` unused by reception |
| **Insurance** | Method string | No claim engine on this path |
| **Cash** | Yes | `payment_method=cash` |
| **Transfer** | Yes | `payment_method=transfer` |
| **Credit** | No (as tender) | Billing ledger CREDIT only |
| **Wallet** | No | Marketplace `WALLET_FUTURE` label only |

### 2.7 Stack B / C (adjacent — not Reception collect)

- Billing: invoices, mark-paid, refunds, tax records — **no RBAC on many routes**; does not update `biz_payments`.
- Gateway: mock Stripe/VNPay/MoMo — auto-complete; separate `payments` table.
- Marketplace: QR payment + webhook idempotency — separate `mp_payments`.

---

## 3. Part 2 — Payment domain model (logical)

Target conceptual model for M2 (maps to **existing** tables where possible; gaps marked).

### Payment

| Attribute | Maps to today |
|-----------|---------------|
| id | `BizPayment.id` |
| order_id | `BizPayment.order_id` |
| invoice_id | `BizPayment.invoice_id` |
| method | `BizPayment.payment_method` |
| amount | `BizPayment.amount` |
| receipt_number | `BizPayment.receipt_number` |
| paid_at | `BizPayment.paid_at` |
| created_by | `BizPayment.created_by` |
| status | Derived via order/invoice/summary (no column on BizPayment) |

### PaymentItem

| Intent | Today |
|--------|-------|
| Line-level payment allocation | **Missing** — payment is whole-invoice amount only |

### PaymentMethod

| Intent | Today |
|--------|-------|
| Catalog of tenders | Allow-list tuple `PAYMENT_METHODS` — **not** a DB entity on Stack A |
| Stack B | `payment_methods` table (tokenized cards etc.) — unused by reception |

### Receipt

| Intent | Today |
|--------|-------|
| Printable fiscal document | **No table** — `receipt_number` + client HTML print |
| Idempotency key reuse | Often same as `receipt_number` |

### Refund

| Intent | Today |
|--------|-------|
| Reverse BizPayment | **Missing** on Stack A |
| Elsewhere | `Refund` / `RefundRecord` on Stack B |

### PaymentStatus

| Intent | Today |
|--------|-------|
| Explicit enum | **Missing** — free strings + computed summary |

### OutstandingBalance

| Intent | Today |
|--------|-------|
| Computed | `order_total − sum(BizPayment.amount)` in `payment_summary_for_order` |
| Persisted balance row | **Missing** |

### Audit

| Intent | Today |
|--------|-------|
| Biz | `BizWorkflowAudit` (`payment.record`, `order.mark_paid`, `invoice.create`) |
| Reception | `write_reception_audit` (`payment_collected`, `order_created`) |

---

## 4. Related documents

- `docs/PAYMENT_STATE_MACHINE.md`
- `docs/PAYMENT_API_SPEC.md`
- `docs/PAYMENT_UI_FLOW.md`
- `docs/PAYMENT_GAP_ANALYSIS.md`
- `docs/RECEPTION_M2_API.md` (foundation contracts)
