# Staging UAT — Release 9.0

**Environment:** `https://staging.dxcon.com.vn` / `https://app-staging.dxcon.com.vn` / `https://api-staging.dxcon.com.vn`  
**Accounts:** see `docs/STAGING_PILOT_ACCOUNTS.md` (vault only).  
**Do not mark PASS without evidence.**

Template fields for every case: Actual result | PASS/FAIL | Evidence | Blocker severity

---

## UAT-S01 Patient login

| | |
|---|---|
| Role | PATIENT |
| URL | `https://app-staging.dxcon.com.vn/login` |
| Prerequisite | Staging deployed; patient account bootstrapped |
| Steps | 1. Open login. 2. Sign in with staging patient. 3. Confirm redirect to `/app/patient`. 4. Confirm STAGING banner. |
| Expected | Auth succeeds; banner visible; no production API host |

---

## UAT-S02 Browse published service

| | |
|---|---|
| Role | PATIENT |
| URL | `/app/patient/book` or public `/services` |
| Prerequisite | Marketplace listings seeded |
| Steps | Open service catalogue; select a published listing. |
| Expected | Real API data or honest empty state; no fake metrics |

---

## UAT-S03 Generate quotation

| | |
|---|---|
| Role | PATIENT |
| URL | Booking wizard quotation step |
| Steps | Select service/provider; request quotation. |
| Expected | Quotation returned from server; amounts consistent |

---

## UAT-S04 Hold appointment slot

| | |
|---|---|
| Role | PATIENT |
| Steps | Select slot; confirm hold timer (~10 min). Wait or release. |
| Expected | Slot held then released/expired per server policy |

---

## UAT-S05 Confirm booking

| | |
|---|---|
| Role | PATIENT |
| Steps | Confirm booking after quotation + slot. |
| Expected | Booking created; visible under patient bookings |

---

## UAT-S06 Payment pending / manual-test state

| | |
|---|---|
| Role | PATIENT |
| URL | `/app/patient/payments` |
| Steps | Initiate payment; observe UI and status. |
| Expected | No live VNPay/MoMo claim; `MOCK_TEST` not usable; MANUAL_BANK_QR or “configuration required” / pay-later per policy |

---

## UAT-S07 Create linked order

| | |
|---|---|
| Role | PATIENT / system |
| Steps | After booking, confirm order appears in `/app/patient/orders`. |
| Expected | Order linked to booking; honest status |

---

## UAT-S08 Reception confirms order

| | |
|---|---|
| Role | RECEPTION |
| URL | `/app/reception` |
| Steps | Login; locate order; confirm/register as per workspace. |
| Expected | Order confirmed; no cross-tenant orders visible |

---

## UAT-S09 Collector receives assignment

| | |
|---|---|
| Role | COLLECTOR |
| URL | `/app/collector` |
| Steps | Open jobs/route; find assignment for the order. |
| Expected | Assignment listed or honest empty state |

---

## UAT-S10 Collector verifies patient

| | |
|---|---|
| Role | COLLECTOR |
| Steps | Open job; verify patient identity fields (synthetic). |
| Expected | Verification step recorded; no real PHI |

---

## UAT-S11 Specimen collected and labelled

| | |
|---|---|
| Role | COLLECTOR / LAB |
| Steps | Record collection; generate/assign barcode. |
| Expected | Specimen status updated; barcode present |

---

## UAT-S12 Transport event recorded

| | |
|---|---|
| Role | COLLECTOR / OPERATIONS |
| Steps | Record transport/custody event (simulated OK on staging). |
| Expected | Timeline entry created |

---

## UAT-S13 Laboratory receives specimen

| | |
|---|---|
| Role | LAB |
| URL | `/app/lab/specimens` or accession |
| Steps | Mark received at lab. |
| Expected | Received status; timeline updated |

---

## UAT-S14 Accession created

| | |
|---|---|
| Role | LAB |
| URL | `/app/lab/accession` |
| Steps | Create accession for specimen. |
| Expected | Accession ID; linked specimen |

---

## UAT-S15 Simulated analyzer result ingested

| | |
|---|---|
| Role | LAB / system |
| Steps | Ingest simulated analyzer result for staging only. |
| Expected | Result preliminary; **not** auto-released |

---

## UAT-S16 Result remains preliminary

| | |
|---|---|
| Role | PATIENT |
| URL | `/app/patient/results` |
| Steps | Login as patient before validation/release. |
| Expected | Preliminary result **not** visible to patient |

---

## UAT-S17 Technician validates

| | |
|---|---|
| Role | LAB |
| URL | `/app/lab/result-review` |
| Steps | Explicit validation action. |
| Expected | Validated; still not released |

---

## UAT-S18 Doctor approves

| | |
|---|---|
| Role | DOCTOR |
| URL | `/app/doctor/review` |
| Steps | Explicit approval. |
| Expected | Approved; still requires explicit release |

---

## UAT-S19 Report explicitly released

| | |
|---|---|
| Role | DOCTOR |
| URL | `/app/doctor/reports` |
| Steps | Explicit release action. |
| Expected | Versioned release; audit event |

---

## UAT-S20 Patient sees released report only

| | |
|---|---|
| Role | PATIENT |
| URL | `/app/patient/results` |
| Steps | Open results after release. |
| Expected | Released report visible; drafts hidden |

---

## UAT-S21 PDF access authorized

| | |
|---|---|
| Role | PATIENT |
| Steps | Download PDF. |
| Expected | Auth required; not a public unauthenticated URL |

---

## UAT-S22 Verification token works

| | |
|---|---|
| Role | Any / public verify route |
| Steps | Use verification token/QR for released report. |
| Expected | Valid for released report only |

---

## UAT-S23 Patient isolation

| | |
|---|---|
| Role | PATIENT A then PATIENT B |
| Steps | Attempt IDOR on A's order/result as B. |
| Expected | 403/404; no data leak |

---

## UAT-S24 Tenant isolation

| | |
|---|---|
| Role | Admin Org A / Org B |
| Steps | Cross-tenant ID access. |
| Expected | Denied |

---

## UAT-S25 Logout and back-button protection

| | |
|---|---|
| Role | Any |
| Steps | Logout; press back; hit protected URL. |
| Expected | Login redirect; no clinical flash |

---

## Gate

**UAT_PASS** only when all 25 cases PASS with evidence on staging.
