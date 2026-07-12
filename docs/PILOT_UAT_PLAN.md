# Pilot UAT plan

Manual UAT for Production Sprint 1. Record pass/fail per case.

## UAT-01 Public website

- Open `https://dxcon.com.vn`
- Verify navigation links (Services, Solutions, Partners, Pricing, Contact)
- Verify Sign In navigates to application login
- Verify Book Demo and Contact
- Verify responsive layout (desktop, tablet, mobile)

## UAT-02 Admin login

- Login as admin pilot account
- Verify session restore after refresh
- Verify organization context in header
- Open `/app/admin` dashboard
- Open `/app/admin/patients` and `/app/admin/orders`
- Logout

## UAT-03 Doctor authorization

- Login as doctor
- View `/app/doctor/patients` and `/app/doctor/reports`
- Attempt `/app/admin` — expect `/forbidden` or redirect

## UAT-04 Clinic owner

- Login as clinic owner
- View `/app/clinic/patients` and `/app/clinic/orders`
- Verify billing/report pages show honest empty state if API context missing

## UAT-05 Lab user

- Login as lab manager
- View `/app/lab` dashboard and `/app/lab/samples`
- Verify no cross-tenant data visible

## UAT-06 Collector

- Login as collector
- View `/app/collector` and `/app/collector/jobs`
- Verify reports routes denied

## UAT-07 Patient

- Login as patient
- View `/app/patient/orders` and `/app/patient/results`
- Verify only own data (or honest empty state)

## Sign-off

| Role | Tester | Date | Result |
|------|--------|------|--------|
| Admin | | | |
| Doctor | | | |
| Clinic | | | |
| Lab | | | |
| Collector | | | |
| Patient | | | |

See also [UAT_PRODUCTION_PILOT.md](./UAT_PRODUCTION_PILOT.md) for executable checklist format.
