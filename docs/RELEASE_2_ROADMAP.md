# DxCon Release 2.0 Roadmap

**Branch:** `release/v2.0.0`  
**Base:** Release 1 freeze tip (`v1.0.0` / `cda364d`)  
**Status:** Initialized — roadmap only  
**Business logic:** **Not started**  
**Release 1:** Frozen — hotfix only (`docs/RELEASE_1_FREEZE.md`)

---

## Purpose

Release 2 extends the frozen clinical platform with payment, documents, queue handoffs, full role workflows, Patient Portal, and Flutter Mobile depth. This document defines milestones only. Implementation begins only after explicit milestone kickoff.

---

## Milestone structure (capability tracks)

| Track | Focus |
|-------|--------|
| **Reception M2** | Payment → receipt → barcode → QR → lab queue handoff |
| **Laboratory** | Lab queue intake through laboratory workflow depth |
| **Collector** | Sample queue and collector field/ops workflow |
| **Doctor** | Doctor review and clinical workflow surfaces |
| **Patient Portal** | Patient-facing results, bookings, payments UX |
| **Mobile** | Flutter Mobile Phase 2+ |

---

## Ordered milestones

### Milestone 1 — Reception Payment

Collect payment against laboratory orders created in Reception M1. Outstanding balance, tender types, payment confirmation, and order status transition to paid / partially paid. No barcode/QR yet.

**Depends on:** Release 1 Reception M1 (frozen)  
**Out of scope:** Receipt print polish (M2), barcode/QR (M3–M4)

---

### Milestone 2 — Receipt

Issue and reprint payment / order receipts for Reception. Idempotent receipt generation, printable/PDF or HTML receipt surface, audit of who printed when.

**Depends on:** Milestone 1  
**Out of scope:** Barcode/QR payloads on receipt (may link later)

---

### Milestone 3 — Barcode

**Status:** Implemented (Step 5) — see `docs/BARCODE_MODULE.md`

Generate and display specimen / order barcodes for Reception documents and labels. Scan-ready encoding consistent with lab accession expectations.

**Depends on:** Milestones 1–2 (order + payment context)  
**Out of scope:** QR alternate encoding (M4)

---

### Milestone 4 — QR

**Status:** Implemented (Step 6) — see `docs/QR_MODULE.md`

Generate and display QR codes for order / requisition / patient handoff as required by Reception document pack.

**Depends on:** Milestone 3 patterns where shared  
**Out of scope:** Patient Portal deep links (later)

---

### Milestone 5 — Lab Queue

**Status:** Implemented (Step 7) — see `docs/LAB_QUEUE_MODULE.md`

Reception → Laboratory queue handoff confirmation. Order appears on lab intake queue with required identifiers (order code, patient, tests, barcodes as applicable).

**Depends on:** M1–M4 as needed for handoff packet  
**Out of scope:** Full lab accession/validation depth (M7)

---

### Milestone 6 — Sample Queue

**Status:** Implemented (Step 8) — see `docs/SAMPLE_QUEUE_MODULE.md`

Collector / sample-ops queue: orders ready for collection, assignment, and status through specimen drawn / ready for transport.

**Depends on:** Lab/collection contracts from Release 1; M5 handoff where applicable  
**Out of scope:** Full collector mobile field app (M8 / M11)

---

## Reception M2 RC freeze

**RC:** `2.0.0-rc1` — `docs/RELEASE_2_RC_REPORT.md`  
Gates: typecheck / M2 lint / auth / build / payment·receipt·barcode·queue regressions — PASS (2026-07-26).

---

### Milestone 7 — Laboratory workflow

End-to-end laboratory operational depth on Release 2 line: receipt → accession → results entry → technical/medical validation → release readiness, aligned with frozen clinical gates.

**Depends on:** M5 lab queue  
**Out of scope:** Instrument middleware mega-integrations (Release 3+)

---

### Milestone 8 — Collector workflow

Collector role workflow completion: queue → collect → transport → lab arrival confirmation, web and/or ops surfaces defined for Release 2.

**Depends on:** M6 sample queue  
**Out of scope:** Full offline Flutter collector (overlap with M11)

---

### Milestone 9 — Doctor workflow

Doctor workspace: review released/pending results, acknowledgements, clinical notes surfaces as scoped for Release 2 (no AI auto-release).

**Depends on:** M7 laboratory release path  
**Out of scope:** Telehealth / AI interpretation productization (later)

---

### Milestone 10 — Patient Portal

Patient-facing portal: view orders/results where released, appointments/bookings, payment status as scoped for Release 2.

**Depends on:** Auth freeze (unchanged pattern), M1–M2 payment/receipt facts, M7 release  
**Out of scope:** Native mobile parity (M11)

---

### Milestone 11 — Flutter Mobile

Flutter Mobile beyond Phase 1 foundation: patient and/or collector field workflows, push-ready architecture, offline-safe reads hardening.

**Depends on:** Phase 1 foundation (Release 1); portal/collector contracts from M8–M10 as applicable  
**Out of scope:** Full white-label multi-app store launch (Release 3+)

---

## Delivery principles

1. **Do not modify Release 1** except via hotfix policy.  
2. **Auth remains frozen** — use existing `useAuth` / AppShell; no bootstrap redesign.  
3. **Admin unchanged** unless a milestone explicitly owns Admin scope (none of M1–M11 by default).  
4. **One milestone kickoff at a time** unless Release Manager approves parallel tracks.  
5. **No business logic in this initialization** — docs and branch only.

---

## Explicit non-actions (this init)

- No payment/receipt/barcode/QR/lab/collector/doctor/portal/mobile feature code  
- No schema migrations for Release 2  
- No merge back into `release/v1.0.0`  
- No Release 3 implementation

---

## References

- `docs/RELEASE_1_FREEZE.md`
- `docs/PROJECT_MASTER_ROADMAP.md`
- `docs/release-2/README.md`
- `docs/AUTH_FREEZE.md`
- `docs/RELEASE_FREEZE_REPORT.md`
