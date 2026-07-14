# Production / Staging UAT Package — Sprint 6 & 7 (Release 9)

**Release:** 9.0  
**Execute on staging first** (`staging.dxcon.com.vn` / `app-staging.dxcon.com.vn`).  
**Do not mark PASS without evidence.**  
**No real PHI. No production passwords in git.**

Base host placeholders:

- Public: `https://staging.dxcon.com.vn` (or production apex after cutover)
- App: `https://app-staging.dxcon.com.vn`
- API: `https://api-staging.dxcon.com.vn`

---

## UAT-01 Public website

| Field | Value |
|---|---|
| Prerequisite | Staging/public frontend deployed |
| Account role | None |
| URL | `/` |
| Steps | Open homepage; verify landing content; click Sign In |
| Expected result | 200; Sign In targets application `/login` |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical if fail |

## UAT-02 Login and session restore

| Field | Value |
|---|---|
| Prerequisite | Pilot account |
| Account role | Any authorized role |
| URL | `/login` |
| Steps | Login; confirm workspace redirect; refresh; confirm session |
| Expected result | Real auth; no demo banner; session restored |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-03 Admin workspace

| Field | Value |
|---|---|
| Prerequisite | Admin account |
| Account role | ADMIN |
| URL | `/app/admin` |
| Steps | Open admin; verify menu permissions; open organizations |
| Expected result | Loads; no fake metrics; permission-filtered nav |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-04 Patient service discovery

| Field | Value |
|---|---|
| Prerequisite | Patient account; listings seeded |
| Account role | PATIENT |
| URL | `/app/patient/book` or public `/services` |
| Steps | Browse services/providers |
| Expected result | Real API data or honest empty state |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-05 Quotation

| Field | Value |
|---|---|
| Prerequisite | Service + provider selected |
| Account role | PATIENT |
| URL | booking wizard quotation step |
| Steps | Request quotation; verify priced breakdown |
| Expected result | Server-priced quotation |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-06 Slot hold

| Field | Value |
|---|---|
| Prerequisite | Quotation available |
| Account role | PATIENT |
| URL | booking slot step |
| Steps | Hold slot; confirm expiry behavior |
| Expected result | Hold created then expires/releases |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-07 Booking confirmation

| Field | Value |
|---|---|
| Prerequisite | Slot held |
| Account role | PATIENT |
| URL | booking confirm step |
| Steps | Confirm booking |
| Expected result | Booking/order created |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-08 Payment pending / manual QR state

| Field | Value |
|---|---|
| Prerequisite | Booking requiring payment |
| Account role | PATIENT |
| URL | `/app/patient/payments` |
| Steps | Open payment; observe provider state |
| Expected result | No false live gateway claim; manual QR / pending / config-required as policy allows |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical if mock payment settles in production |

## UAT-09 Order creation

| Field | Value |
|---|---|
| Prerequisite | Booking confirmed |
| Account role | PATIENT |
| URL | `/app/patient/orders` |
| Steps | Verify order appears with correct status |
| Expected result | Order linked to service/provider |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-10 Specimen creation and collection

| Field | Value |
|---|---|
| Prerequisite | Order ready for collection |
| Account role | COLLECTOR / LAB |
| URL | collector/lab specimen routes |
| Steps | Create/collect specimen; assign barcode |
| Expected result | Specimen lifecycle advances |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-11 Transport and accession

| Field | Value |
|---|---|
| Prerequisite | Collected specimen |
| Account role | LAB / OPERATIONS |
| URL | lab accession / logistics |
| Steps | Transport if needed; accession at lab |
| Expected result | Accession recorded; timeline updated |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-12 Simulated analyzer result

| Field | Value |
|---|---|
| Prerequisite | Staging simulator enabled |
| Account role | LAB |
| URL | lab analyzers / result intake |
| Steps | Ingest simulated analyzer preliminary result |
| Expected result | Result enters queue; **not** auto-released |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical if auto-release |

## UAT-13 Technician validation

| Field | Value |
|---|---|
| Prerequisite | Preliminary/pending result |
| Account role | LAB technician |
| URL | `/app/lab/result-review` |
| Steps | Explicit validate |
| Expected result | Status → validated; not patient-visible as final |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-14 Doctor approval

| Field | Value |
|---|---|
| Prerequisite | Technician-validated result |
| Account role | DOCTOR |
| URL | `/app/doctor/review` |
| Steps | Explicit approve |
| Expected result | Approved; still not released until UAT-15 |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-15 Explicit report release

| Field | Value |
|---|---|
| Prerequisite | Doctor-approved result |
| Account role | DOCTOR / release-authorized |
| URL | `/app/doctor/reports` |
| Steps | Explicit release |
| Expected result | Versioned release; pre-release hidden from patient |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-16 Patient released-result access

| Field | Value |
|---|---|
| Prerequisite | Released report |
| Account role | PATIENT (owner) |
| URL | `/app/patient/results` |
| Steps | View results |
| Expected result | Only released results visible |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-17 PDF authorization

| Field | Value |
|---|---|
| Prerequisite | Released report |
| Account role | PATIENT |
| URL | PDF download from results |
| Steps | Download PDF; attempt unauthenticated URL |
| Expected result | Auth required; no public PHI PDF |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-18 Verification token

| Field | Value |
|---|---|
| Prerequisite | Released report with token |
| Account role | Verifier / PATIENT |
| URL | `/verify-report/[token]` |
| Steps | Validate token |
| Expected result | Token verifies released report only |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

## UAT-19 Patient isolation

| Field | Value |
|---|---|
| Prerequisite | Two patients with distinct orders |
| Account role | PATIENT A then PATIENT B |
| URL | orders/results |
| Steps | Attempt IDOR / cross-patient access |
| Expected result | 403/404; no cross-patient data |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-20 Tenant isolation

| Field | Value |
|---|---|
| Prerequisite | Two organizations |
| Account role | ADMIN Org A / ADMIN Org B |
| URL | `/app/admin/*` |
| Steps | Attempt cross-tenant ID access |
| Expected result | Denied; tenant scoping enforced |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | Critical |

## UAT-21 Logout and back-button protection

| Field | Value |
|---|---|
| Prerequisite | Authenticated session |
| Account role | Any |
| URL | protected page → logout |
| Steps | Logout; browser back; open `/app` |
| Expected result | No protected content; redirect to login; session cleared |
| Actual result | |
| PASS/FAIL | |
| Evidence/screenshot | |
| Blocker severity | High |

---

## UAT sign-off

| Gate | PASS/FAIL | Date | Tester |
|---|---|---|---|
| Staging UAT complete | | | |
| Critical path production subset | | | |
