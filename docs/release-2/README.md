# Release 2 — Milestone Structure

**Branch:** `release/v2.0.0`  
**Status:** Structure only — no implementation  
**Roadmap:** `docs/RELEASE_2_ROADMAP.md`

---

## Tracks

| Track | Folder | Release 2 milestones |
|-------|--------|----------------------|
| Reception M2 | [reception-m2/](./milestones/reception-m2/) | M1 Payment, M2 Receipt, M3 Barcode, M4 QR, M5 Lab Queue |
| Laboratory | [laboratory/](./milestones/laboratory/) | M5 Lab Queue (shared), M7 Laboratory workflow |
| Collector | [collector/](./milestones/collector/) | M6 Sample Queue, M8 Collector workflow |
| Doctor | [doctor/](./milestones/doctor/) | M9 Doctor workflow |
| Patient Portal | [patient-portal/](./milestones/patient-portal/) | M10 Patient Portal |
| Mobile | [mobile/](./milestones/mobile/) | M11 Flutter Mobile |

---

## Rules

1. Release 1 is frozen — hotfix only (`docs/RELEASE_1_FREEZE.md`).  
2. Do not implement business logic until a milestone is explicitly kicked off.  
3. Auth freeze remains active.  
4. Prefer feature branches off `release/v2.0.0` named `feature/r2-mN-<slug>`.
