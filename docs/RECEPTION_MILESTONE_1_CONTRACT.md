# Reception Milestone 1 — Patient & Order API Contract

Base: `https://api.dxcon.com.vn` · Prefix: `/api/v1/reception/workspace`  
Auth: Bearer JWT (Reception/Admin roles) · Header: `X-Organization-ID` (sent; backend currently role-scoped, not org-filtered)  
Out of scope: payment, barcode, lab handoff.

| UI action | Endpoint | Request | Response | Status | Persisted |
|-----------|----------|---------|----------|--------|-----------|
| Search patient | `GET /search?q&limit&page` | `q`: phone, patient_code, national_id, full_name, or `dxcon:patient:<code>` | `{ success, data: Patient[], pagination }` | 200, 401, 403 | — |
| Create patient | `POST /patients/register` | `full_name*`, `phone*`, `date_of_birth`, `gender`, `email`, `national_id`, `address`, `patient_code?`, `force?` | `{ success, data: { patient, queue_entry, qr_payload, warnings } }` | 201; 409 duplicate; 400 validation | patients, profile, queue |
| Duplicate resolve | same + `force:true` or select existing | Soft 409 warnings `{ field, message, patient_code }` | Soft skip via force; hard uniqueness may still 400 | — | |
| Patient profile / reopen | `GET /patients/:code` | path code | patient + `orders[]` (summary) | 200, 404 | — |
| Get order (reopen) | `GET /orders/:ref` | path order_code or id | `{ order, pricing: { subtotal, discount, total } }` | 200, 404 | — |
| Reopen fallback | `GET /patients/:code` then match `orders[]` | used when `GET /orders/:ref` returns 404 (API not yet deployed) | order summary + totals from profile | 200 | — |
| Search catalog | `GET /tests?q&category&limit&page` | text + category package filter | tests: `id, code, name, category, sample_type, price, turnaround_hours` | 200 | — |
| Create order | `POST /orders` | `patient_code*`, `test_catalog_ids*` (UUIDs), `discount?`, `note?` | `{ order, invoice, pricing }` — **pricing authoritative** | 201, 400, 401, 403 | order, items, invoice, queue |

**Authoritative pricing:** only `data.pricing` / order totals from create or GET. Client estimates are preview-only, labeled as such.  
**Packages:** catalog `category` selection (no backend package expansion).  
**Permissions:** roles `RECEPTION`, `ADMIN`, `SUPER_ADMIN`, `SYSTEM_ADMIN`.
