# DxCon Project Manual

**Version:** 1.0  
**Last updated:** 2026-07-05  
**Purpose:** Single repository-based source of truth for how DxCon is built, tested, released, and operated.

---

## 1. Project Mission

DxCon is an **Intelligent Diagnostic Services Platform (IDSP)** — not a traditional LIS. It orchestrates diagnostic commerce, logistics, clinical workflow, and governed result delivery across a multi-sided healthcare ecosystem: patients, doctors, laboratories, clinics, collectors, and partners.

**North star:** One platform for all healthcare operations — from order intake and specimen logistics through lab execution, doctor review, and patient release — with full auditability and production-grade security.

See also: [`docs/rfc/RFC-0001-DXCON-PLATFORM.md`](rfc/RFC-0001-DXCON-PLATFORM.md), [`docs/SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md).

---

## 2. Current Operating Model

| Layer | Location | Notes |
|-------|----------|-------|
| **Product backlog** | [`docs/PRODUCT_BACKLOG.md`](PRODUCT_BACKLOG.md) | Epics, stories, priority, status |
| **Release plan** | [`docs/RELEASE_PLAN.md`](RELEASE_PLAN.md) | Versioned milestones |
| **Sprints** | [`docs/sprints/`](sprints/) | One markdown file per sprint |
| **Sprint template** | [`docs/SPRINT_TEMPLATE.md`](SPRINT_TEMPLATE.md) | Required sections for every sprint |
| **Launch checklist** | [`docs/LAUNCH_CHECKLIST.md`](LAUNCH_CHECKLIST.md) | Pre-production gates |
| **Engineering backlog** | [`docs/ENGINEERING_BACKLOG.md`](ENGINEERING_BACKLOG.md) | P0–P3 technical debt and security |
| **Verification** | `backend/scripts/verify_*.py`, `scripts/verify_project_governance.py` | Automated PASS/FAIL gates |
| **Reports** | `backend/generated_release/` | JSON artifacts from verify scripts |

**Workflow**

1. Pick work from `PRODUCT_BACKLOG.md` or an active sprint doc.
2. Scope changes in a sprint file before coding (goal, scope, API/data impact).
3. Implement with minimal diff; no drive-by refactors.
4. Run targeted verify scripts and unit tests.
5. Update sprint status and backlog when done.
6. Commit with sprint-defined message; push after PASS.

**Governance rule:** Decisions live in the repo — not in chat history. Chat prompts initiate work; documents record intent and outcomes.

---

## 3. Coding Rules

- **Minimal scope** — Fix only what the sprint or bug ticket requires.
- **Match conventions** — Follow patterns in surrounding modules (naming, imports, error handling).
- **No bare `except`** — Catch specific exceptions; log with context.
- **No secrets in code** — Use environment variables; fail fast in production if missing.
- **No `db.create_all()` for production schema** — Use additive SQL migrations in `backend/migrations/`.
- **Blueprint registration** — New routes via existing blueprint patterns; avoid duplicate route paths.
- **Static assets** — CSS in `backend/app/static/css/dxcon.css`; branding in `backend/app/static/branding/`.
- **Comments** — Only for non-obvious business logic or regulatory requirements.

---

## 4. API Rules

- **Prefix:** `/api/v1/` for REST APIs unless explicitly legacy.
- **Auth:** JWT + role decorators on all non-public endpoints.
- **Public routes** — Must be listed and reviewed (`backend/scripts/verify_public_routes.py`).
- **Response shape** — Prefer `{ "success": true, "data": ... }` for new APIs where established.
- **Versioning** — Breaking changes require a new version prefix or documented deprecation window.
- **No duplicate routes** — One path + method combination per handler (`verify_blueprint_registry.py`).
- **OpenAPI** — Maintain `/api/v1/openapi.json` accuracy for partner integrations.
- **Idempotency** — Payment, order state transitions, and webhooks must be safe to retry.

Reference: [`docs/API_OVERVIEW.md`](API_OVERVIEW.md), [`docs/API_REFERENCE.md`](API_REFERENCE.md).

---

## 5. Database Migration Rules

- **Location:** `backend/migrations/` — numbered SQL files (`001_*.sql`, `002_*.sql`, …).
- **Additive first** — Prefer `ADD COLUMN IF NOT EXISTS`, new tables, indexes; avoid destructive DDL in hot paths.
- **Dual support** — Code must tolerate SQLite (tests) and PostgreSQL (production) where introspection is used.
- **Apply in verify/UAT** — `backend/scripts/uat_lib.py` `apply_additive_migrations()` for test databases.
- **No schema change without migration file** — Even nullable columns need a tracked migration.
- **Rollback** — Document reverse steps in sprint or release notes; prefer forward-fix migrations over DROP.
- **MDM / master data** — Import via MDM engine (`/app/mdm`); do not hand-edit production reference tables.

---

## 6. Testing Rules

| Type | Command / Script | When |
|------|------------------|------|
| Compile | `python3 -m compileall backend/app backend/scripts backend/tests` | Every change |
| Unit tests | `python3 -m unittest discover -s backend/tests` | Before commit |
| Module verify | `python3 backend/scripts/verify_<module>.py` | Per sprint deliverable |
| UAT role scripts | `verify_uat_collector.py`, `verify_uat_lab.py`, etc. | Workflow changes |
| Launch UI | `verify_launch_ui.py` | UI shell changes |
| MDM | `verify_mdm.py` | Master data changes |
| Governance | `python3 scripts/verify_project_governance.py` | Doc pack changes |

- **TESTING=True** and in-memory SQLite for most unit tests.
- **PostgreSQL** required for UAT and production-parity scripts (`DATABASE_URL` in `backend/.env`).
- New features should include or extend a verify script when automated check is practical.
- Critical/High bugs: fix + regression verify. Medium/Low: backlog entry in sprint or `PRODUCT_BACKLOG.md`.

---

## 7. Release Rules

- **Release plan:** [`docs/RELEASE_PLAN.md`](RELEASE_PLAN.md) defines 1.0 → 3.0 milestones.
- **Branch:** `main` is integration; feature branches merge after PASS verify.
- **Commit messages** — Imperative, sprint-aligned (e.g. `Master Data Management Platform`, `UAT 2-5 - Workflow Validation and Critical Fixes`).
- **Pre-release gates:**
  - `verify_enterprise_hardening_pack10.py`
  - `verify_staging_stack.py` or `smoke_test_staging_stack.py`
  - `final_ga_smoke.py`
- **Artifacts** — Store JSON reports under `backend/generated_release/`.
- **Tagging** — Semantic versions (`v1.0.0-pilot`, `v1.1.0`) after launch checklist sign-off.
- **Release notes** — Update `/release-management/notes` or sprint doc deliverables section.

---

## 8. Rollback Rules

- **Trigger conditions** — See [`docs/GO_LIVE_RUNBOOK.md`](GO_LIVE_RUNBOOK.md) and [`docs/ROLLBACK_RUNBOOK.md`](ROLLBACK_RUNBOOK.md).
- **Application rollback** — Redeploy previous container image / git tag.
- **Database rollback** — Prefer forward migration fix; avoid DROP in production.
- **Maintenance window** — `POST /api/v1/operations/maintenance/enable` before destructive ops.
- **Verify after rollback** — Health (`/health`, `/ready`, `/live`), smoke test, pilot status.
- **Incident** — Follow [`docs/INCIDENT_RUNBOOK.md`](INCIDENT_RUNBOOK.md); post-mortem within 48h for Sev-1.

---

## 9. Bug Handling Rules

| Severity | Definition | Action |
|----------|------------|--------|
| **Critical** | Data loss, security breach, blocked production workflow | Fix immediately; hotfix commit |
| **High** | Role workflow broken, incorrect clinical/billing state | Fix in current sprint |
| **Medium** | UX degradation, non-blocking errors | Backlog + next sprint |
| **Low** | Cosmetic, docs, nice-to-have | Backlog |

- Log bugs in sprint doc or `PRODUCT_BACKLOG.md` story notes.
- UAT failures → `backend/generated_release/UAT_*_REPORT.json` + optional `BUG_BACKLOG.md`.
- Every bug fix: root cause, verify script or test, status update in backlog.

---

## 10. Production Deployment Rules

- **Guide:** [`docs/DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md), [`docs/GO_LIVE_RUNBOOK.md`](GO_LIVE_RUNBOOK.md).
- **Environment:** `APP_ENV=production`, `LOG_FORMAT=json`, secrets from platform (Render/etc.).
- **Required vars:** [`docs/REQUIRED_ENVIRONMENT_VARIABLES.md`](REQUIRED_ENVIRONMENT_VARIABLES.md).
- **Deploy order:** maintenance → migrate → deploy → health probes → smoke → disable maintenance.
- **No demo seed in production** — Real users and master data only.
- **Worker:** Background jobs must be configured before GA (not placeholder worker).
- **Monitoring:** Prometheus, Grafana, Alertmanager per `deployment/monitoring/`.

---

## 11. Security Baseline

- No hardcoded `SECRET_KEY` / `JWT_SECRET_KEY` in production.
- Privileged roles assigned by admin only — not self-registration.
- Logistics, collector, shipment APIs require authentication.
- Rate limiting enabled in production.
- CORS explicitly configured — no wildcard in production.
- API keys stored hashed; one-time exposure on create.
- Run `backend/scripts/security_preflight.py` before release.
- Compliance reference: [`docs/COMPLIANCE_GUIDE.md`](COMPLIANCE_GUIDE.md).

---

## 12. Audit Baseline

- **Application audit** — `audit_logs` table; `write_audit()` in `backend/app/core/audit.py`.
- **Request tracing** — `request_id` / `trace_id` on all requests; JSON logs in production.
- **MDM audit** — Import and sync events via MDM audit module.
- **Immutable clinical actions** — Order status, chain of custody, result release logged with actor and timestamp.
- **Retention** — Follow tenant policy and regulatory minimums (document per deployment).
- **Verification** — Enterprise hardening packs check audit and log redaction (passwords, tokens).

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [`PRODUCT_BACKLOG.md`](PRODUCT_BACKLOG.md) | Epics and stories |
| [`RELEASE_PLAN.md`](RELEASE_PLAN.md) | Version roadmap |
| [`LAUNCH_CHECKLIST.md`](LAUNCH_CHECKLIST.md) | Go-live gates |
| [`SPRINT_TEMPLATE.md`](SPRINT_TEMPLATE.md) | Sprint structure |
| [`OPERATIONS_GUIDE.md`](OPERATIONS_GUIDE.md) | Day-2 operations |
| [`BRAND_GUIDELINES.md`](BRAND_GUIDELINES.md) | Visual identity |
