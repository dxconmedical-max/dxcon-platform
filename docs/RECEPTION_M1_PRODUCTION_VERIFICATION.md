# Reception M1 — Production Verification Report

**Role:** Production QA  
**Date (UTC):** 2026-07-25  
**Environment:** Production web `https://dxcon.com.vn` → API `https://api.dxcon.com.vn`  
**Account:** `demo-reception-01@demo.dxcon.test`  
**Verdict:** **FAIL — STOPPED**  
**Stopped at:** Refresh / reopen persistence verification (post–order create)  
**Fixes applied:** None

---

## Executive summary

The Reception M1 happy path **succeeded through order creation** on production. Immediately after create, the UI auto-refresh `GET …/orders/<order_code>` **failed with browser `responseStatus: 0`**, and the confirmation screen showed:

> **Network error — check your connection.**

Per Production QA policy (**if any issue exists → STOP**), verification halted.  
**No automatic fixes** were attempted. Refresh-browser / reopen / persistence confirmation steps were **not completed**.

---

## Synthetic identifiers

| Item | Value |
|------|--------|
| Patient name | `E2E RECEPTION TEST 20260725125002` |
| Patient phone | `0999125002` |
| **Patient code** | **`P-20260725125042-ED8778`** |
| Selected test | `CBC-DFC9FFF6` — Complete Blood Count — catalog preview **150.000 ₫** |
| **Order code** | **`ORD-20260725130537-03F985`** |
| Order status (from create UI) | `payment_pending` |
| Authoritative total (from create UI) | **150.000 ₫** (subtotal 150.000 ₫ · discount 0 ₫) |

---

## Step results

| # | Step | Result | Evidence |
|---|------|--------|----------|
| 1 | Reception Login | **PASS** | Login **200**, `/auth/me` **200**, landed `/app/reception` |
| 2 | Search Patient | **PASS** | Search `0901` → `PT001` / Nguyen Van A |
| 3 | Create Patient | **PASS** | `POST …/patients/register` **201** |
| 4 | Search Again | **PASS** | Created patient listed; workflow URL `?patient=P-20260725125042-ED8778` |
| 5 | Open Test Catalog | **PASS** | `GET …/tests?limit=100` **200** |
| 6 | Add Test | **PASS** | Selected `CBC-DFC9FFF6` |
| 7 | Pricing | **PASS** | Preview (not final) **150.000 ₫**; labeled non-final |
| 8 | Create Order | **PASS** | `POST …/orders` **201**; order code + status shown |
| 9 | Refresh Browser | **NOT RUN** | Stopped after issue on post-create verify |
| 10 | Re-open Order | **NOT RUN** | Stopped |
| 11 | Verify Order Persistence | **FAIL** | Auto `GET …/orders/ORD-…` **status 0**; UI network error |

---

## Exact root cause (stop condition)

**Root cause:**  
After successful `POST /api/v1/reception/workspace/orders` (**HTTP 201**, ~1020 ms), the confirmation step’s follow-up read:

`GET https://api.dxcon.com.vn/api/v1/reception/workspace/orders/ORD-20260725130537-03F985`

completed in the browser with **`responseStatus: 0`**, **`duration: 128 ms`**, and the UI rendered **“Network error — check your connection.”**

This is **not** a create failure (order already exists in UI with code/status/totals). It is a **post-create order-read / refresh verification failure** that blocks certified persistence proof under this checklist.

**Failure class:** Client-observed failed/aborted order detail fetch (`status 0`) immediately after create — distinct from HTTP 4xx/5xx with a JSON body.

---

## Network / API capture (session)

| Call | Status | Duration | Notes |
|------|--------|----------|-------|
| `POST /api/v1/auth/login` | **200** | ~2770 ms | Reception login |
| `GET /api/v1/auth/me` | **200** | ~286 ms | Session |
| `GET /api/v1/auth/capabilities` | **200** | ~225 ms | Capabilities |
| `GET …/search?q=0901&limit=25` | **200** | ~224 ms | Existing patient search |
| `GET …/search?q=0999125002&limit=25` | **200** | ~236 ms | Duplicate probe before create |
| `POST …/patients/register` | **201** | ~606 ms | Create patient |
| `GET …/patients/P-20260725125042-ED8778` | **200** | ~217 ms | Persistence confirm on create |
| `GET …/search?q=P-20260725125042-ED8778` | **200** | ~229 ms | Search again |
| `GET …/tests?limit=100&page=1` | **200** | ~357 ms | Catalog |
| `POST …/orders` | **201** | ~1020 ms | Create order |
| `GET …/orders/ORD-20260725130537-03F985` | **0** | ~128 ms | **STOP — network error** |

---

## Console

No separate uncaught JavaScript exception string was captured beyond the app’s controlled **Network error** banner on the order-created step.

---

## Screenshots

| File | Step |
|------|------|
| `docs/verification-artifacts/reception-m1-prod/01-login-reception-workspace.png` | Login → Reception workspace |
| `docs/verification-artifacts/reception-m1-prod/02-search-existing-patient.png` | Search existing patient |
| `docs/verification-artifacts/reception-m1-prod/03-create-and-search-patient.png` | Create + search synthetic patient |
| `docs/verification-artifacts/reception-m1-prod/04-catalog-open.png` | Catalog open |
| `docs/verification-artifacts/reception-m1-prod/05-test-selected-pricing.png` | Test selected + preview price |
| `docs/verification-artifacts/reception-m1-prod/06-order-created-network-error.png` | Order created + **network error** (stop) |

---

## Unexpected / related observations (non-fix)

1. Production Reception UI currently shows a **3-step** M1 flow (`Patient` → `Tests & order` → `Order created`), not the 5-step Preview branch labels — still reachable and functional through create.
2. Catalog contains many similar CBC codes (test/demo seed density).
3. Order create UI already displayed patient, test line, status, and authoritative total **before** the failed GET refresh.

---

## STOP decision

| Field | Value |
|-------|--------|
| Policy | If any issue exists → **STOP**; report only; no auto-fix |
| Stopped | Yes |
| Remaining steps | Refresh browser, reopen order, persistence certification |
| Auto-fix | **None** |
| Milestone 2 | Not started |

---

## Recommended human follow-up (outside this report)

1. Reproduce `GET /api/v1/reception/workspace/orders/ORD-20260725130537-03F985` with a Reception session (browser Retry / Network tab).
2. Determine whether status `0` is abort/race, CORS, timeout mislabel, or gateway drop.
3. Re-run steps 9–11 only after order-read succeeds; do not treat create- alone as persistence proof.

---

## Sign-off

| Field | Value |
|-------|--------|
| Production QA verdict | **FAIL** |
| Stopped at | Post-create order read / persistence verify |
| Exact issue | `GET …/orders/ORD-20260725130537-03F985` → browser status **0**; UI **Network error** |
| Synthetic patient | `P-20260725125042-ED8778` |
| Synthetic order | `ORD-20260725130537-03F985` |
