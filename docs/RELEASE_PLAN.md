# DxCon Release Plan

**Last updated:** 2026-07-05  
**Planning horizon:** Release 1.0 Pilot → Release 3.0 Ecosystem

---

## Release 1.0 — Pilot Operational Release

**Target:** Q3 2026  
**Tag:** `v1.0.0-pilot`  
**Theme:** Real clinics and labs running core diagnostic workflow on PostgreSQL.

### Goals

- End-to-end workflow: reception → collection → lab → doctor review → patient portal
- Master data loaded via MDM
- Launch UI product shell for all roles
- UAT PASS for Collector, Lab, Doctor, Patient, Reception
- Production deployment with monitoring, backup, and security preflight

### In Scope

| Area | Deliverables |
|------|--------------|
| Patient / Order | Registration, orders, invoices, barcodes |
| Collection / Lab | Accept, custody, QC gate, results |
| Doctor / Patient | Review, release, portal data |
| MDM | 18 entity imports, admin UI |
| Launch UI | `/home`, `/login`, `/app/*` role shells |
| Ops | Health probes, audit logs, demo seed disabled in prod |

### Exit Criteria

- [`LAUNCH_CHECKLIST.md`](LAUNCH_CHECKLIST.md) — all Critical items checked
- UAT scripts PASS on PostgreSQL
- `verify_enterprise_hardening_pack10.py` PASS
- Pilot: ≥1 clinic + ≥1 lab live

### Sprints

- SPRINT-001 MDM (DONE)
- SPRINT-002 Launch UI (DONE)
- SPRINT-003 Business Stabilization (IN_PROGRESS)

---

## Release 1.1 — Business Stabilization

**Target:** Q4 2026  
**Tag:** `v1.1.0`  
**Theme:** Production hardening and workflow completeness.

### Goals

- Close P0 items in [`ENGINEERING_BACKLOG.md`](ENGINEERING_BACKLOG.md)
- Payment gateway live (or pilot billing integration)
- PDF reports and print workflows
- MDM legacy sync complete
- Duplicate route and monitoring gaps resolved

### In Scope

- Alembic / migration discipline
- Authenticated logistics APIs
- Real payment reconciliation
- Performance baseline for order pipeline
- Bug backlog Medium+ from pilot

### Exit Criteria

- 30-day pilot with no Critical incidents
- Security preflight 8/8 PASS
- Blueprint registry 0 duplicate routes

---

## Release 1.2 — AI + Notification

**Target:** Q1 2027  
**Tag:** `v1.2.0`  
**Theme:** Intelligent assistance and proactive patient engagement.

### Goals

- Critical result notifications (SMS/email/push)
- AI result interpretation v2 with governance
- Doctor advisory UX in production workflow
- Notification delivery monitoring and retries

### In Scope

- Notification templates and preferences
- AI audit and human-in-the-loop gates
- Alertmanager rules for clinical SLA
- Patient notification center in portal

### Exit Criteria

- Notification delivery SLA ≥99% in staging
- AI governance checklist signed
- No unauthenticated AI admin endpoints

---

## Release 2.0 — SaaS + Mobile

**Target:** Q2–Q3 2027  
**Tag:** `v2.0.0`  
**Theme:** Multi-tenant commercial SaaS with mobile field apps.

### Goals

- Tenant self-service provisioning
- Subscription billing
- Flutter collector and patient apps in app stores
- White-label branding per tenant
- Commercial launch checklist complete

### In Scope

- SaaS onboarding funnel
- Mobile collector: accept, scan, custody
- Mobile patient: orders, reports, pay
- Regional deployment option
- Partner marketplace v1

### Exit Criteria

- 3+ paying tenants
- Mobile apps approved (iOS + Android)
- [`LAUNCH_CHECKLIST.md`](LAUNCH_CHECKLIST.md) SaaS section PASS

---

## Release 3.0 — Ecosystem

**Target:** 2028  
**Tag:** `v3.0.0`  
**Theme:** Networked diagnostic economy — federation, population health, marketplace.

### Goals

- Cross-tenant federation and data sharing (governed)
- Population health dashboards
- Marketplace booking and partner revenue share
- Device gateway and instrument network at scale
- Regional cloud and compliance packs

### In Scope

- Federation platform production
- Data warehouse pipelines
- Partner ecosystem APIs
- Enterprise analytics and executive suite
- Certification and training center

### Exit Criteria

- Ecosystem verify suite PASS
- Documented partner onboarding &lt; 30 days
- Compliance guide aligned with target markets

---

## Release Governance

| Activity | Owner | Artifact |
|----------|-------|----------|
| Sprint planning | Engineering | `docs/sprints/SPRINT-*.md` |
| Release sign-off | Product + Ops | `backend/generated_release/*_REPORT.json` |
| Go-live | Ops | [`GO_LIVE_RUNBOOK.md`](GO_LIVE_RUNBOOK.md) |
| Rollback | On-call | [`ROLLBACK_RUNBOOK.md`](ROLLBACK_RUNBOOK.md) |

Reference: [`ROADMAP_v2.md`](ROADMAP_v2.md) for completed phase history.
