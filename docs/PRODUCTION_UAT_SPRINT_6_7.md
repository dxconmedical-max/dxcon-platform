# Production UAT Package — Sprint 6 & 7

**Release:** 8.1 · **Sprint:** 9
**Environment:** Execute on **staging** (`uat.dxcon.com.vn`) before production.
**Do not mark PASS until executed with evidence.**

---

## UAT-01 Public Website

| Field | Value |
| --- | --- |
| Prerequisite | Staging or production frontend deployed |
| Account role | None (unauthenticated) |
| Route | `https://uat.dxcon.com.vn/` |
| Steps | 1. Open homepage. 2. Verify hero, services, pricing sections render. 3. Click Sign In. |
| Expected result | Homepage loads without auth. Sign In opens `app.uat.dxcon.com.vn/login`. No clinical data visible. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if fail |

---

## UAT-02 Login and Session Restore

| Field | Value |
| --- | --- |
| Prerequisite | Pilot account exists on staging |
| Account role | Any (e.g. `doctor@uat.dxcon.local`) |
| Route | `https://app.uat.dxcon.com.vn/login` |
| Steps | 1. Enter valid credentials. 2. Confirm redirect to role workspace. 3. Refresh page. 4. Confirm session restored without re-login. |
| Expected result | Login succeeds. Session persists on refresh. No mock/demo banner. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if fail |

---

## UAT-03 Admin Workspace

| Field | Value |
| --- | --- |
| Prerequisite | Admin account |
| Account role | ADMIN |
| Route | `/app/admin` |
| Steps | 1. Login as admin. 2. Navigate to admin workspace. 3. Verify sidebar menu items match permissions. 4. Open organizations page. |
| Expected result | Admin workspace loads. Menu filtered by capabilities. No fake metrics. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if fail |

---

## UAT-04 Patient Booking

| Field | Value |
| --- | --- |
| Prerequisite | Patient account; marketplace listings seeded |
| Account role | PATIENT |
| Route | `/app/patient/book` |
| Steps | 1. Login as patient. 2. Open booking wizard. 3. Select service and provider. 4. Proceed through wizard steps. |
| Expected result | Booking wizard loads. Services/providers from real API or honest empty state. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if fail |

---

## UAT-05 Quotation and Slot Hold

| Field | Value |
| --- | --- |
| Prerequisite | UAT-04 in progress; slot engine configured |
| Account role | PATIENT |
| Route | `/app/patient/book` (quotation step) |
| Steps | 1. Select date/time slot. 2. Request quotation. 3. Verify slot hold (10 min). 4. Wait for hold expiry and confirm slot released. |
| Expected result | Quotation returned with pricing. Slot held then released. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if fail |

---

## UAT-06 Payment Pending or Verified Test Flow

| Field | Value |
| --- | --- |
| Prerequisite | Order created; payment adapter configured |
| Account role | PATIENT |
| Route | `/app/patient/payments` |
| Steps | 1. Create order with payment required. 2. Attempt payment. 3. Verify "Payment configuration required" if no live gateway. 4. Verify pay-later only if server policy allows. |
| Expected result | No false claim of live VNPay/MoMo. Test adapter not usable in staging/production strict env. Manual bank QR or pay-later shown per policy. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if mock payment works in production |

---

## UAT-07 Order Creation

| Field | Value |
| --- | --- |
| Prerequisite | UAT-05 quotation accepted |
| Account role | PATIENT |
| Route | `/app/patient/book` (confirm step) |
| Steps | 1. Confirm booking. 2. Verify order created in `/app/patient/orders`. 3. Check order status. |
| Expected result | Order appears with correct status. Linked to selected service/provider. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if fail |

---

## UAT-08 Specimen and Lab Workflow

| Field | Value |
| --- | --- |
| Prerequisite | Order with specimen; lab account |
| Account role | LAB |
| Route | `/app/lab/specimens`, `/app/lab/accession` |
| Steps | 1. Login as lab tech. 2. Accession specimen from order. 3. Verify barcode assignment. 4. Check specimen timeline. |
| Expected result | Specimen accessioned. Barcode generated. Timeline updated. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if fail |

---

## UAT-09 Technician Validation

| Field | Value |
| --- | --- |
| Prerequisite | Result entered for accessioned specimen |
| Account role | LAB (technician) |
| Route | `/app/lab/result-review` |
| Steps | 1. Open technician review queue. 2. Select pending result. 3. Perform explicit validation action. 4. Verify status changes to validated (not auto-released). |
| Expected result | Explicit validation required. No automatic release. Status transitions logged. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if auto-release occurs |

---

## UAT-10 Doctor Approval

| Field | Value |
| --- | --- |
| Prerequisite | UAT-09 validated result |
| Account role | DOCTOR |
| Route | `/app/doctor/review` |
| Steps | 1. Login as doctor. 2. Open review queue. 3. Review validated result. 4. Perform explicit approval. |
| Expected result | Doctor must explicitly approve. Result not released until UAT-11. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if auto-release occurs |

---

## UAT-11 Explicit Report Release

| Field | Value |
| --- | --- |
| Prerequisite | UAT-10 approved result |
| Account role | DOCTOR or authorized release role |
| Route | `/app/doctor/reports` |
| Steps | 1. Open approved report. 2. Perform explicit release action. 3. Verify report version created. 4. Confirm pre-release result not accessible to patient. |
| Expected result | Release is explicit separate action. Version incremented. Pre-release hidden from patient. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if fail |

---

## UAT-12 Patient Released-Result Access

| Field | Value |
| --- | --- |
| Prerequisite | UAT-11 report released |
| Account role | PATIENT (owner of order) |
| Route | `/app/patient/results` |
| Steps | 1. Login as patient who owns the order. 2. Open results. 3. Verify only released results visible. 4. Confirm pre-release results not shown. |
| Expected result | Only explicitly released results accessible. No draft/pending results. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if pre-release visible |

---

## UAT-13 PDF and Verification Token

| Field | Value |
| --- | --- |
| Prerequisite | UAT-11 released report |
| Account role | PATIENT |
| Route | `/app/patient/results` → PDF download |
| Steps | 1. Download PDF for released report. 2. Verify PDF requires auth (not public URL). 3. Check verification QR/token on report. 4. Validate token via verification endpoint. |
| Expected result | PDF access protected. Verification token valid for released report only. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if PDF publicly accessible |

---

## UAT-14 Patient Isolation

| Field | Value |
| --- | --- |
| Prerequisite | Two patient accounts with separate orders |
| Account role | PATIENT A, PATIENT B |
| Route | `/app/patient/results`, `/app/patient/orders` |
| Steps | 1. Login as Patient A. 2. Note order/result IDs. 3. Logout. 4. Login as Patient B. 5. Attempt to access Patient A's order/result by ID manipulation. |
| Expected result | Patient B cannot see Patient A's data. API returns 403/404. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if fail |

---

## UAT-15 Tenant Isolation

| Field | Value |
| --- | --- |
| Prerequisite | Two org accounts in different tenants |
| Account role | ADMIN Org A, ADMIN Org B |
| Route | `/app/admin/organizations`, `/app/admin/patients` |
| Steps | 1. Login as Admin Org A. 2. Note org/patient IDs. 3. Switch or login as Admin Org B. 4. Attempt cross-tenant ID access. |
| Expected result | Cross-tenant access denied. Each org sees only its data. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | Critical if fail |

---

## UAT-16 Logout and Back-Button Protection

| Field | Value |
| --- | --- |
| Prerequisite | Authenticated session |
| Account role | Any |
| Route | Any protected route → logout |
| Steps | 1. Login and navigate to protected page. 2. Click logout. 3. Press browser back button. 4. Attempt to access protected route directly. |
| Expected result | Back button does not show protected content. Redirect to login. Session fully cleared. |
| Actual result | |
| PASS/FAIL | |
| Screenshot/evidence | |
| Blocker severity | High if fail |
