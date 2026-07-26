# Milestone 4 — QR

**Track:** Reception M2  
**Status:** Implemented (Release 2 Step 6)

Generate QR codes for payment, VNPay, order/patient handoff, sample, and tracking.

**Depends on:** Milestone 3 patterns where shared (sample QR uses barcode gate).

## Delivered

- QR engine (`qr_engine.py`) with payment / VNPay / static / dynamic / sample / tracking
- Verification API
- Page: `/app/reception/m2/qr`
- Tests: `backend/tests/test_qr_engine.py`
- Doc: `docs/QR_MODULE.md`

**Out of scope:** Live VNPay settlement, Patient Portal deep links.
