# DxCon Product Backlog

**Last updated:** 2026-07-05  
**Status legend:** `TODO` · `IN_PROGRESS` · `DONE`  
**Priority legend:** `Critical` · `High` · `Medium` · `Low`

Work is tracked here and in [`docs/sprints/`](sprints/). Engineering security items remain in [`ENGINEERING_BACKLOG.md`](ENGINEERING_BACKLOG.md).

---

## Epic: Patient Management

| Story | Status | Priority |
|-------|--------|----------|
| Patient registration with demographics and contact | DONE | Critical |
| Patient search by name, phone, code | DONE | Critical |
| Patient edit form (reception) | IN_PROGRESS | High |
| Patient merge / duplicate detection | TODO | Medium |
| Patient QR health card | DONE | Medium |
| Patient history timeline | TODO | Medium |

---

## Epic: Order Management

| Story | Status | Priority |
|-------|--------|----------|
| Create order from reception with test catalog | DONE | Critical |
| Order status workflow (draft → collected → lab → review → released) | IN_PROGRESS | Critical |
| Order barcode generation on payment | IN_PROGRESS | High |
| Order search and filters | DONE | High |
| Print request form HTML | IN_PROGRESS | High |
| Order cancellation and refund rules | TODO | Medium |

---

## Epic: Payment & Invoice

| Story | Status | Priority |
|-------|--------|----------|
| Invoice generation on order | DONE | Critical |
| Mark payment received (reception) | DONE | Critical |
| Patient invoice list and pay action | DONE | High |
| Payment gateway integration (live) | TODO | High |
| Refund and credit note | TODO | Medium |
| Revenue reporting by partner | TODO | Low |

---

## Epic: Sample Collection

| Story | Status | Priority |
|-------|--------|----------|
| Collector job list and route view | DONE | Critical |
| Accept collection / handover | IN_PROGRESS | Critical |
| Chain of custody updates | IN_PROGRESS | Critical |
| In-transit sample tracking | IN_PROGRESS | High |
| Home collection scheduling | TODO | High |
| Cold-chain temperature logging | TODO | Medium |

---

## Epic: Laboratory Workflow

| Story | Status | Priority |
|-------|--------|----------|
| Sample receive at lab | DONE | Critical |
| Testing in progress state | DONE | Critical |
| QC complete gate before review | IN_PROGRESS | Critical |
| Instrument result import | TODO | High |
| Lab workload dashboard | DONE | Medium |
| TAT and SLA alerts | TODO | Medium |

---

## Epic: Result & Report

| Story | Status | Priority |
|-------|--------|----------|
| Enter lab results | DONE | Critical |
| Report validation queue | DONE | High |
| PDF report generation | TODO | High |
| Report release to patient portal | IN_PROGRESS | Critical |
| Critical result flagging | DONE | High |
| Historical report archive | TODO | Medium |

---

## Epic: Doctor Review

| Story | Status | Priority |
|-------|--------|----------|
| Doctor workbench with pending reviews | DONE | Critical |
| Sign-off and release action | DONE | Critical |
| Critical results alert panel | DONE | High |
| AI interpretation advisory (read-only) | DONE | Medium |
| Multi-doctor assignment | TODO | Medium |
| Digital signature capture | TODO | Low |

---

## Epic: Patient Portal

| Story | Status | Priority |
|-------|--------|----------|
| Patient login and role routing | DONE | Critical |
| Orders and status view | DONE | Critical |
| Reports list with real data | IN_PROGRESS | Critical |
| Invoices and payment status | DONE | High |
| Profile and demographics | DONE | Medium |
| Notifications preferences | TODO | Medium |

---

## Epic: Master Data Management

| Story | Status | Priority |
|-------|--------|----------|
| MDM registry (18 entity types) | DONE | Critical |
| CSV/XLSX import engine | DONE | Critical |
| MDM admin UI (`/app/mdm`) | DONE | Critical |
| Import templates and validation | DONE | High |
| MDM dashboard and reports | DONE | High |
| Legacy sync to operational tables | IN_PROGRESS | High |
| MDM API (`/api/v1/mdm/*`) | DONE | Medium |

**Sprint:** [`sprints/SPRINT-001-MDM.md`](sprints/SPRINT-001-MDM.md)

---

## Epic: CRM

| Story | Status | Priority |
|-------|--------|----------|
| CRM pipeline dashboard | DONE | Medium |
| Lead and account records | TODO | High |
| Clinic onboarding workflow | TODO | High |
| Partner contract tracking | TODO | Medium |
| Sales activity log | TODO | Low |

---

## Epic: Logistics

| Story | Status | Priority |
|-------|--------|----------|
| Transport box and QR scan | DONE | High |
| Shipment status API | DONE | High |
| Logistics v2 dashboard | DONE | Medium |
| Route optimization | TODO | Medium |
| SLA breach notifications | TODO | High |
| Partner capacity scheduling | TODO | Medium |

---

## Epic: AI

| Story | Status | Priority |
|-------|--------|----------|
| AI copilot shell (doctor/lab) | DONE | Medium |
| Clinical CDS advisory endpoints | DONE | Medium |
| AI operations monitoring | DONE | Low |
| Result interpretation v2 | TODO | High |
| Population health insights | DONE | Low |
| AI governance and audit trail | TODO | High |

---

## Epic: Integration

| Story | Status | Priority |
|-------|--------|----------|
| OpenAPI and developer portal | DONE | High |
| HL7/FHIR adapter framework | IN_PROGRESS | High |
| Webhook delivery and retries | DONE | High |
| Partner API keys | DONE | Critical |
| LIS instrument bridge | TODO | High |
| Marketplace service catalog sync | TODO | Medium |

---

## Epic: Mobile

| Story | Status | Priority |
|-------|--------|----------|
| Flutter app scaffold (`mobile/dxcon_mobile`) | DONE | High |
| Mobile auth and API config | DONE | High |
| Collector mobile workflow | TODO | Critical |
| Patient mobile portal | TODO | High |
| Push notifications | TODO | High |
| App store release pipeline | TODO | Medium |

---

## Epic: Commercial Launch

| Story | Status | Priority |
|-------|--------|----------|
| Marketing home (`/home`) | DONE | High |
| Brand guidelines and assets | DONE | High |
| Project governance pack | IN_PROGRESS | Critical |
| Launch checklist execution | TODO | Critical |
| Pilot customer onboarding (3+ sites) | TODO | Critical |
| Pricing and quote workflow | TODO | High |
| SaaS billing and tenant provisioning | TODO | High |

**Sprint:** [`sprints/SPRINT-002-LAUNCH-UI.md`](sprints/SPRINT-002-LAUNCH-UI.md), [`sprints/SPRINT-003-BUSINESS-STABILIZATION.md`](sprints/SPRINT-003-BUSINESS-STABILIZATION.md)

---

## Backlog Hygiene

1. Update story status when sprint closes.
2. New epics require entry in [`RELEASE_PLAN.md`](RELEASE_PLAN.md).
3. Critical items block Release 1.0 pilot sign-off.
