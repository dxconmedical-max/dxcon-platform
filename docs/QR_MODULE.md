# QR Module — Release 2 Step 6

**Status:** Implemented  
**Scope:** Payment QR, VNPay QR, static/dynamic QR, sample QR, tracking QR, verification, tests  
**Out of scope:** Live VNPay merchant settlement, Patient Portal deep links  

---

## Payload scheme

| Kind | Prefix / form | Notes |
|------|---------------|--------|
| Payment | `dxcon:pay:{order}:{amount}:{currency}` | Desk QR tender |
| VNPay | `dxcon:vnpay:{txn}:{amount_x100}:{order}:{sig}` | Compact + sandbox URL in meta |
| Static | `dxcon:patient:` / `dxcon:order:` | Stable identifiers |
| Dynamic | `dxcon:dyn:{purpose}:{order}:{nonce}:{exp}:{sig}` | HMAC + TTL (default 15m) |
| Sample | `dxcon:sample:{specimen}` | Requires paid order (barcode gate) |
| Tracking | `dxcon:track:{order}` | + optional `track_url` |

Images: PNG data URLs via `qrcode`.

---

## Service

`backend/app/reception_workspace/qr_engine.py`

- `build_qr_bundle` / `preview_qr_html`
- `build_payment_qr`, `build_vnpay_qr`, `build_static_qrs`, `build_dynamic_qr`, `build_sample_qrs`, `build_tracking_qr`
- `verify_qr_payload` — format, signature, expiry, optional order binding

Env (optional): `DXCON_QR_SECRET`, `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET`, `PUBLIC_BASE_URL`

---

## APIs (`/api/v1/reception/workspace`)

| Method | Path |
|--------|------|
| GET | `/orders/:ref/qr?kinds=&amount=&images=&preview=` |
| GET | `/orders/:ref/qr/preview` |
| POST | `/qr/verify` — `{ payload, order_ref? }` |
| GET | `/qr/kinds` |

---

## UI

- Page: `/app/reception/m2/qr` (`?order=ORD-…`)
- Component: `QrWorkbench`
- Module: `apps/web/src/modules/reception-m2/qr/`
- Client: `@/lib/api/reception` QR helpers

---

## Verification

Server-side `verify_qr_payload` checks:

- Recognized `dxcon:` scheme (or VNPay HTTPS URL)
- Dynamic / VNPay compact HMAC
- Dynamic expiry
- Optional order binding when `order_ref` supplied

---

## Tests

`backend/tests/test_qr_engine.py`
