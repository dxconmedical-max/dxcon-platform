# Release Notes — DxCon v2.0.0-rc1 (Reception M2)

**Status:** Release Candidate  
**Branch:** `release/v2.0.0`  
**Date:** 2026-07-26  
**Auth:** Frozen (unchanged)

---

## Summary

Reception Milestone 2 product track is packaged as **Release 2 RC1**: payment desk engine, receipts, barcodes, QR, laboratory queue, and sample queue — layered on the frozen Release 1 clinical baseline.

Release 1 (`v1.0.0`) remains frozen for hotfix-only changes.

---

## What’s in (Reception M2)

| Area | Highlights |
|------|------------|
| **Payment** | Partial-aware collect, method validation, payment history, desk state machine |
| **Receipt** | Auto-issue on pay; preview / print / thermal / PDF / reprint / cancel + audit |
| **Barcode** | Order / sample / collection / patient labels; browser + thermal printers |
| **QR** | Payment, VNPay (sandbox), static/dynamic, sample, tracking + verify |
| **Lab queue** | Waiting → processing → completed → verified; priority; live refresh |
| **Sample queue** | Collected → transport → received → sorting → laboratory → completed; history + audit |

### UI routes

`/app/reception/m2/{payment,receipt,barcode,qr,lab-queue,sample-queue}`

### Migrations

`017_reception_receipts.sql`, `018_lab_queue.sql`, `019_sample_queue.sql`

---

## What’s not

- Live VNPay merchant settlement
- Full laboratory accession / medical validation depth (R2 M7)
- Full collector mobile field app (R2 M8 / M11)
- Auth runtime changes
- Release 1 GA reopen

---

## Quality (RC gates)

- Typecheck **PASS**
- Reception M2 lint **PASS**
- Auth freeze Vitest + guard **PASS**
- Reception Vitest **PASS** (50)
- Production build **PASS**
- Backend engine regressions **PASS** (payment / receipt / barcode / QR / lab queue / sample queue)
- Reception workspace suite **PASS**

See `docs/RELEASE_2_RC_REPORT.md` for the full gate table.

---

## Upgrade notes

1. Deploy from `release/v2.0.0` after RM-approved commit/PR.
2. Apply SQL migrations `017`–`019` on Postgres before enabling receipt/queue features.
3. Keep `API_AUTH_GATE_ENABLED=true`, `DEMO_MODE=false`.
4. Optional: `DXCON_QR_SECRET`, `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET` for QR/VNPay.
5. Smoke M2 paths per `docs/RELEASE_2_GO_LIVE_CHECKLIST.md`.

---

## Rollback

- **Web:** previous Vercel deployment / prior commit on `release/v2.0.0`.
- **API:** prior Render deploy; leave new tables in place (additive) or drop only if unused.
- **Auth:** unchanged — no auth rollback path required for this RC.
