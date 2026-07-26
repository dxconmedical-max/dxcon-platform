# Payment Gap Analysis — Reception M2 Step 2

**Purpose:** Existing vs missing backend support, blockers, implementation order  
**No implementation in this document’s step.**

---

## 1. Existing backend support (Reception cash desk)

| Capability | Support | Evidence |
|------------|---------|----------|
| Order + line pricing | Yes | `BizOrder` / items, create order API |
| Order-level discount | Yes | `discount` on create; `_recalc_order_totals` |
| Invoice unpaid/paid | Yes | `BizInvoice` |
| Full payment collect | Yes | `POST …/payment` → `collect_payment` |
| Methods cash/transfer/qr/pos/corporate/insurance | Yes | Allow-list strings |
| Idempotent collect | Yes | Key ↔ `receipt_number` |
| Outstanding computation | Yes | `payment_summary_for_order` |
| Receipt number | Yes | `BizPayment.receipt_number` |
| Audit | Yes | biz + reception audits |
| Queue sync on pay | Yes | `PAYMENT_PENDING` → `PAID` |
| Gate documents/lab on paid | Yes | barcode / lab-handoff guards |
| Frontend client | Yes | `collectReceptionPayment` etc. |
| Interim UI | Yes | `OrderSteps` payment section |

---

## 2. Missing backend support (for full narrative workflow)

| Capability | Gap | Severity for M2 Payment kickoff |
|------------|-----|----------------------------------|
| VAT on grand total | `tax` always `null`; no Biz tax column | Medium (display/compliance) |
| Insurance adjudication | Method label only | Medium/High if sold as benefit |
| Partial payments | **Supported (Step 3 Payment Engine)** | Closed for desk collect |
| PaymentItem / multi-tender | Absent | Low for v1 full-pay |
| Receipt entity / reprint API | Client-only print | Low |
| Refund / void BizPayment | Absent on Stack A | High for ops after go-live |
| Credit tender | Absent | Low unless required |
| Wallet | Absent | Low (future) |
| Formal PaymentStatus enum | Free strings | Low |
| Structured error codes | String messages | Medium (UI mapping) |
| Unified ledger with Stack B | Parallel stacks | High (architecture debt) |
| RBAC on `/billing` & `/payments` | Missing | **P0 security** (adjacent) |
| Real PSP for reception | Not on Stack A | N/A if cash-desk only |
| SQL migrations for Stack B tables | ORM-only risk | Ops |

---

## 3. Production blockers

| ID | Blocker | Why |
|----|---------|-----|
| PB-001 | Stack confusion | Calling billing/gateway APIs for reception orders will not update `biz_payments` / order paid gates |
| PB-002 | No reception refund | Mis-collect cannot be reversed on Stack A |
| PB-003 | Adjacent open billing/payment APIs | Unauthenticated high-risk surfaces (if exposed) |
| PB-004 | Partial flag vs behavior | UI/report mentions `partial`/`waived` but collect forbids partial — support risk |
| PB-005 | VAT/insurance narrative vs code | Marketing/compliance claims must not assume VAT/insurance math |
| PB-006 | KI-R1-001 class issues | Post-create order GET flaky in prod history — payment desk depends on reliable GET |
| PB-007 | Mock PSPs elsewhere | Must not be used as reception payment path in production |

**Not a blocker for full-pay cash/transfer desk:** core `POST …/payment` path itself exists and is covered by backend tests.

---

## 4. Recommended implementation order

When Payment domain kickoff is approved (still **not** this step):

1. **Lock Stack A as sole Reception payment ledger** — document in runbooks; forbid Stack B for desk.  
2. **UI extract** — move collect/receipt from `OrderSteps` into `modules/reception-m2/payment` + `receipt` **without** duplicating mappers (use existing client).  
3. **Harden client UX** — loading, timeout, idempotent retry, full-amount lock (per `PAYMENT_UI_FLOW.md`).  
4. **Structured error codes** (additive API fields — non-breaking).  
5. **Decide product:** keep full-pay-only **or** design partial + PaymentItem (schema + API change).  
6. **Receipt polish** — reprint from GET order; optional PDF later.  
7. **Refund design** (new Stack A capability or controlled admin tool) before expanding tenders.  
8. **VAT / insurance** — only after product + fiscal rules; do not fake in UI.  
9. **Close adjacent auth gaps** on billing/gateway routes (security track).  
10. **Then** Lab documents/queue UX (already gated on paid).

---

## 5. What NOT to do

- Do not invent new payment endpoints while Stack A collect works.  
- Do not copy BizPayment mappers into a second service.  
- Do not implement payment UI in this analysis step.  
- Do not modify Release 1 frozen auth.  
- Do not “fix” VAT by hardcoding 10% in the client.

---

## 6. Traceability

| Doc | Role |
|-----|------|
| `PAYMENT_DOMAIN_ANALYSIS.md` | Inventory + logical model |
| `PAYMENT_STATE_MACHINE.md` | Transitions |
| `PAYMENT_API_SPEC.md` | Existing contracts |
| `PAYMENT_UI_FLOW.md` | Screen states |
| `PAYMENT_GAP_ANALYSIS.md` | This file |
