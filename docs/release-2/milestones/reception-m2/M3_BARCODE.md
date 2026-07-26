# Milestone 3 — Barcode

**Track:** Reception M2  
**Status:** Implemented (Release 2 Step 5)

Generate specimen/order/collection barcodes for Reception labels and documents.

**Depends on:** Payment (paid-order gate); collection job for collection barcodes.

## Delivered

- Barcode engine + printer abstraction (`barcode_engine.py`, `printers.py`)
- Label types: order, sample, collection, patient
- Standard + thermal (80mm) preview/print
- Page: `/app/reception/m2/barcode`
- Tests: `backend/tests/test_barcode_engine.py`
- Doc: `docs/BARCODE_MODULE.md`

**Out of scope:** QR product milestone, hardware driver binaries.
