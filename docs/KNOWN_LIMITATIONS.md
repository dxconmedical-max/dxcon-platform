# DxCon Known Limitations

**Phase 10 · Enterprise v1.0.0-rc1**

This document records intentional gaps and deferred work for the v1.0 release candidate. Review before production cutover with real patient data.

---

## Phase 10 Scaffold Modules

- **DxCon Pharmacy** — formulary and dispensing integration planned for v2.
- **DxCon Insurance** — claims adjudication scaffold only.
- **Support Center** — ticket workflow scaffold; use email escalation for RC1.
- **Certification Center** — program definitions only; exams not yet automated.

## Security & Access

- Some logistics and collector API routes may operate without JWT enforcement in development; production must enable full auth (see `ENGINEERING_BACKLOG.md` BL-P0-001).
- Public self-registration can accept privileged roles unless restricted by environment policy (BL-P0-002).
- Demo accounts use a shared password (`DemoPass123!`) — never reuse in production.

## Infrastructure

- Redis may report `DEGRADED` when not configured; queue features fall back gracefully in SQLite/dev mode.
- SMTP and external notification providers are optional; email delivery is not guaranteed in local pilot stacks.
- Object storage defaults to local `STORAGE_PATH`; S3-compatible storage required for multi-node production.

## Data & Schema

- SQLite is supported for tests and verify scripts; production expects PostgreSQL with migrations verified at startup.
- Demo seed data uses prefixed codes (`DEMO-ORD-*`, `DEMO-PAT-*`); do not mix with production patient records.
- Some legacy `orders` and `medical_orders` tables coexist; reporting hubs aggregate both where applicable.

## AI & Clinical

- AI interpretation outputs require human review before clinical release; not a substitute for licensed sign-off.
- Token cost estimates in AI Operations hub are advisory budgeting figures, not billing integration.
- Prompt versions are versioned in-platform but external LLM provider failover is manual.

## Integrations

- Partner adapter sandbox supports HIS/LIS/EMR/ERP stubs; live hospital integrations need per-site certification.
- Webhook dead-letter queue requires operator review; no automatic replay in pilot mode.
- HL7/FHIR advanced standards hub is read-only validation; full bidirectional sync is roadmap work.

## Operations

- Backup jobs may be empty on fresh installs until `POST /api/v1/operations/backups/run` or scheduler seed runs.
- Rollback plans are metadata-only until a deployment record exists via operations checklist.
- Generated release reports under `backend/generated_release/` reflect last verify run, not live runtime unless re-run.

## Pilot UX

- PDF report generation requires completed test results on demo orders.
- QR transport pages display payload text; hardware scanner integration is app-side.
- Executive and pilot dashboards prefer demo-prefixed datasets when full production volume is absent.

---

## Review Cadence

- Update this file when closing backlog items or before each RC promotion.
- Cross-check with `ROADMAP_v2.md` and phase verify reports in `/readiness-pack`.
