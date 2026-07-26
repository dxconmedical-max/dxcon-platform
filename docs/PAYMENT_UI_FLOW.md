# Payment UI Flow — Reception M2 Step 2

**Scope:** Screen flow design only — **no implementation**  
**Reuse:** AppShell, frozen auth, existing `OrderSteps` interim patterns; future pages under `/app/reception/m2/payment`  
**API:** `docs/PAYMENT_API_SPEC.md`

---

## 1. Entry points

```text
Reception home
  → Workflow (R1 M1) → Confirmation (payment_pending)
  → M2 Payment page (architecture placeholder today)
  → Reopen GET /orders/:ref?order=…
```

Prerequisite: order exists with `payment_summary.outstanding_amount > 0` (or show paid/receipt if already paid).

---

## 2. Screen flow (happy path — full payment)

```text
[Loading order]
      ↓
[Payment desk — Outstanding]
      ↓ select method + confirm amount (= outstanding)
[Submitting payment]  (disable double-submit; keep idempotency key)
      ↓ 200 + order_status paid
[Receipt]
      ↓ print / continue
[Documents / Lab Queue]  (barcode → handoff — separate domains)
```

---

## 3. States & screens

### 3.1 Loading

| | |
|--|--|
| **Trigger** | Mount / refresh / reopen |
| **API** | `GET …/orders/:ref` |
| **UI** | Skeleton / spinner; no collect button |
| **Exit success** | Render desk with `payment_summary` |
| **Exit fail** | Failed / timeout → Retry |

### 3.2 Outstanding (unpaid)

| | |
|--|--|
| **Data** | `order_total`, `outstanding_amount`, `discount`, `subtotal`, `tax` (null), methods list |
| **UI** | Method select (cash/transfer/qr/pos/corporate/insurance); amount field default = outstanding; Collect CTA |
| **Rules** | Show banner: partial payments not supported; amount must equal outstanding |
| **Exit** | Collect → Submitting |

### 3.3 Partial payment

| | |
|--|--|
| **Product desire** | Allow amount < outstanding |
| **Actual API** | **400** — not supported |
| **UI design** | Do **not** offer partial slider in v1 UI; if user edits amount below outstanding, **client validate** before POST and show inline error; if server returns partial error, map to Failed with message |
| **Future** | Only enable when `partial_payments_supported === true` |

### 3.4 Full payment (confirm)

| | |
|--|--|
| **UI** | Confirm sheet: method, amount, order code, patient |
| **Action** | POST payment with fresh or stable idempotency key for this attempt |
| **Exit** | Receipt on success |

### 3.5 Receipt

| | |
|--|--|
| **Data** | `payment.receipt_number`, method, amount, `paid_at`, cashier (`created_by`), order code |
| **UI** | Receipt panel; Print (window/HTML — client only); Continue to documents |
| **API** | No receipt GET — use payment payload from collect or GET order |

### 3.6 Failed

| Cause | UI |
|-------|-----|
| 400 validation | Inline / toast with server `error` string |
| 401/403 | Auth error surface (existing AppShell patterns) |
| 404 | Order missing — back to search |
| Network / parse | Generic failure + Retry |

Keep form values; **do not rotate idempotency key** on pure network retry of same attempt (see Timeout/Retry).

### 3.7 Timeout

| | |
|--|--|
| **Client** | `RECEPTION_PAYMENT_TIMEOUT_MS` (30s) |
| **UI** | Timeout message; actions: Retry (same key) \| Refresh order (GET) \| Cancel |
| **Risk** | Server may have committed — always GET order before second Collect with **new** key |

### 3.8 Retry

| Scenario | Idempotency key | Action |
|----------|-----------------|--------|
| Same user attempt after timeout/network | **Reuse** key | POST again → expect success or `idempotent_replay` |
| User changes amount/method after hard failure | **New** key | After GET confirms still unpaid |
| Already paid (replay) | any | Show Receipt; do not collect again |

---

## 4. State → UI matrix

| payment_summary.status | Primary screen | CTA |
|------------------------|----------------|-----|
| `unpaid` | Outstanding | Collect full |
| `partial` | Outstanding + warning | Collect remaining **full** outstanding only (if API ever allows multi-pay history) |
| `paid` | Receipt | Print / Continue |

| order.status | Note |
|--------------|------|
| `payment_pending` | Collect enabled |
| `paid`+ | Receipt / documents |
| other | Not payable — show status |

---

## 5. Wireframe sequence (logical)

```text
┌─────────────────────────────┐
│ Order ORD-… · payment_pending│
│ Subtotal …  Discount …       │
│ Tax —                        │
│ Outstanding 150.000 ₫        │
│ Method [cash ▼]              │
│ Amount [150000] (locked=full)│
│ [ Collect payment ]          │
└─────────────────────────────┘
              │ success
              ▼
┌─────────────────────────────┐
│ Receipt RCT-…                │
│ Paid · cash · 150.000 ₫      │
│ [ Print ] [ Continue → Docs ]│
└─────────────────────────────┘
```

---

## 6. Non-goals for UI (this analysis)

- No insurance claim forms  
- No VAT line editor  
- No wallet top-up  
- No refund desk  
- No implementation of the above screens in this step  

---

## 7. Accessibility / ops notes

- Disable Collect while in-flight  
- Announce success/failure to AT  
- Log correlation: order_code + receipt_number + idempotency_key (no card data — N/A for cash desk methods)
