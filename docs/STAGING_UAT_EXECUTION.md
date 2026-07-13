# Staging UAT Execution — Sprint 6 & 7

**Release:** 8.1
**Environment:** Staging only (`staging.dxcon.com.vn` / `app-staging.dxcon.com.vn`)
**Source cases:** `docs/PRODUCTION_UAT_SPRINT_6_7.md` (adapt URLs to staging)

---

## Pilot account provisioning (no passwords in Git)

Create accounts via staging admin or approved seed script **at deploy time**:

| Role | Email pattern | Workspace |
|---|---|---|
| Admin | `admin+<staging-id>@uat.dxcon.local` | `/app/admin` |
| Reception | `reception+<staging-id>@uat.dxcon.local` | `/app/reception` |
| Collector | `collector+<staging-id>@uat.dxcon.local` | `/app/collector` |
| Lab technician | `lab+<staging-id>@uat.dxcon.local` | `/app/lab` |
| Doctor | `doctor+<staging-id>@uat.dxcon.local` | `/app/doctor` |
| Clinic | `clinic+<staging-id>@uat.dxcon.local` | `/app/clinic` |
| Patient A | `patient-a+<staging-id>@uat.dxcon.local` | `/app/patient` |
| Patient B | `patient-b+<staging-id>@uat.dxcon.local` | `/app/patient` |

**Rules:**
- Use synthetic names only — **no real PHI**
- Generate passwords with a password manager; store in a secure vault (not Git)
- One organization per tenant isolation test (Org A / Org B)
- Document credentials in your team's secure UAT tracker only

---

## One-time account creation process

1. Deploy staging backend with migrations 016–020 applied
2. Run organization + user seed (admin creates org, invites users) OR execute approved staging seed script with env-provided passwords:
   ```bash
   # Example pattern — use your team's approved script, not committed secrets
   STAGING_SEED_PASSWORD="<from-password-manager>" python backend/scripts/seed_staging_pilot.py
   ```
3. Verify login for each role on `https://app-staging.dxcon.com.vn/login`
4. Record account emails (not passwords) in UAT tracker

---

## Execution order

| Phase | UAT cases | Prerequisite |
|---|---|---|
| 1 — Access | UAT-01, UAT-02, UAT-16 | Staging frontend + backend deployed |
| 2 — Admin | UAT-03, UAT-15 | Admin account |
| 3 — Commerce | UAT-04, UAT-05, UAT-06, UAT-07 | Patient account, marketplace seeded |
| 4 — Lab workflow | UAT-08, UAT-09 | Lab account, order with specimen |
| 5 — Clinical governance | UAT-10, UAT-11, UAT-12, UAT-13 | Doctor account, validated results |
| 6 — Isolation | UAT-14, UAT-15 | Two patient + two org accounts |

---

## Staging-specific checks

- [ ] STAGING banner visible (or environment label in UI)
- [ ] `NEXT_PUBLIC_APP_ENV=staging` confirmed in build
- [ ] No production API URL in staging frontend env
- [ ] Payment shows honest state (no live gateway unless staging adapter configured)
- [ ] Password reset pages show disabled message (SMTP not claimed unless configured)

---

## Evidence template

For each UAT case in `docs/PRODUCTION_UAT_SPRINT_6_7.md`:

1. Replace production URLs with staging URLs
2. Fill **Actual result**, **PASS/FAIL**, **Screenshot/evidence**
3. File blockers with severity in UAT tracker

**UAT_PASS** requires all 16 cases PASS on staging with evidence.
