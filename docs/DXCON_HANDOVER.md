# DxCon — Project Handover & Current-State Audit

**Audit date:** 2026-09-08  
**Repository:** `dxconmedical-max/dxcon-platform`  
**Default branch:** `main`  
**Visibility:** public  
**Current source of truth:** repository `main`, not historical chat notes or old deployment commits.

> This document is a handover baseline for a new developer/team. It intentionally distinguishes what is evidenced in the repository from historical project intent. Do not treat an old release note as proof that the current production environment is healthy.

## 1. Executive summary

DxCon is a healthcare/laboratory diagnostics platform whose product direction covers patient/reception workflows, laboratory processing, sample collection, billing/payment, documents/receipts, barcode/QR, AI-assisted clinical decision support, operational workflows, and future collector/mobile/IoT capabilities.

The repository is materially more advanced than the early Flask-only prototype described in historical development conversations. The current `main` tree contains a structured backend, a web application, mobile/application directories, deployment manifests, database migrations, extensive documentation, AI platform components, billing/operations models, and release artifacts.

The immediate handover priority is **not to rewrite the platform**. It is to establish a verified runtime baseline, identify which release is actually deployed, confirm database/Redis/worker state, and then continue from the current architecture without breaking the existing authentication/release freezes.

## 2. Repository structure observed

Top-level areas currently present include:

- `.cursor/` — Cursor project instructions/configuration.
- `.github/` — CI/workflow configuration.
- `apps/` — application/frontend workspace.
- `backend/` — Flask backend and supporting services.
- `deployment/` — deployment assets.
- `docs/` — extensive architecture, release, module, compliance and operational documentation.
- `dxcon_patient_app/` — patient application tree.
- `mobile/` — mobile application tree.
- `scripts/` — project scripts.
- Docker Compose files for development, staging and production.

The repository root therefore represents a multi-surface platform rather than the original single Flask application. The current tree also contains a `backend/app/ai_platform` subsystem and numerous API/model modules.

## 3. Backend architecture

The primary backend entrypoint is the application factory in `backend/app/__init__.py`.

Current application boot sequence:

1. Create Flask application.
2. Load `Config`.
3. Validate configuration.
4. Initialize extensions.
5. Register middleware.
6. Register blueprints.
7. Register error handlers.
8. Finalize observability.
9. Enter application context and run deployment initialization.

This is materially different from the legacy/simple `backend/app.py` prototype, which directly creates a Flask app, defines a minimal `Patient` model and starts port 8000. **Do not use `backend/app.py` as the architectural source of truth without first checking whether it is intentionally retained as a legacy/demo entrypoint.** The production path uses `run:app` through Gunicorn.

Relevant production files:

- `backend/app/__init__.py`
- `backend/production_start.py`
- `backend/gunicorn.conf.py`
- `backend/Dockerfile`
- `backend/render.yaml`
- `docker-compose.production.yml`
- `docker-compose.staging.yml`
- `docker-compose.yml`

## 4. Backend technology

Current pinned/runtime dependencies include:

- Flask 3.1.3
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.1.0
- Flask-JWT-Extended 4.7.1
- Flask-CORS 6.0.2
- Gunicorn 23.0.0
- psycopg2-binary 2.9.12
- SQLAlchemy 2.0.50
- Alembic 1.16.5
- Redis client
- ReportLab
- Pillow
- openpyxl
- bcrypt

The production data path is therefore designed around PostgreSQL, not the early local SQLite prototype.

## 5. Data/model layer

The current repository contains substantially more models than the early MVP notes. Examples observed include:

- AI/CDS models
- alerts
- API platform
- audit logs
- battery events
- billing accounts
- billing adjustments
- billing ledger
- business orders
- booking assignments
- clinic bookings
- clinic departments
- clinic doctors
- plus the patient/order/laboratory/sample/result domain developed earlier.

The complete model inventory should be treated as repository-defined and should be mapped before making schema changes. `backend/migrations/` exists and must be used as the migration source of truth.

## 6. Product workflow currently represented

The release documentation shows a concrete Reception → Collection → Laboratory workflow rather than only CRUD APIs.

The broad business flow is:

`Patient/Clinic → Reception → Order → Payment → Receipt → Barcode/QR → Sample Collection → Collector/Reception handoff → Laboratory Queue → Sample Queue → Result/clinical workflow`

The project also contains separate operational, billing, AI, admin, clinic and application surfaces.

## 7. Reception / Release 2 status

The repository's Release 2 RC report records Reception M2 as **RC READY FOR REVIEW**, not GA. The frozen scope included:

- Payment Engine
- Receipt Module
- Barcode Module
- QR Module
- Laboratory Queue
- Sample Queue

The reported RC quality gates included passing typecheck, Reception M2 lint, auth regression, auth-freeze verification, reception frontend tests, production build, payment/receipt/barcode/QR/lab/sample engine tests, and reception workspace tests.

Important: these are historical release-gate results from the documented RC date. They are not a substitute for a fresh current-main CI/deployment verification.

## 8. Collector / Reception / Lab fixes already made

Recent main-branch history shows important workflow fixes:

- `0c17145...` — merged hotfix to persist and resolve `SampleCollection` on Assign.
- `e345611...` — implementation of the same collection persistence fix.
- `ddca5c4...` — kept Reception create-order controls visible when the catalog is empty.
- `f7b8637...` — merged Collector ← Reception → Lab end-to-end workflow fix.
- `4cbd782...` — fixed home-patient duplicate UUID.
- `9a96872...` — merge preserving `RELEASED` lifecycle, collection-mode routing, desk/field queues and Reception→SampleCollection→Lab workflow.
- `7fb48fe...` — bridged HomeCollection into SampleCollection queues and collector queue semantics.

The last recent commit visible in the repository history at audit time is `0c17145...`, dated 2026-08-10 UTC. Verify the actual deployed SHA separately before promoting anything.

## 9. AI platform

The current backend contains a dedicated `ai_platform` subsystem with components including:

- gateway
- governance
- inference/inference service
- memory
- metrics
- models
- PHI redaction
- prompt registry
- RAG
- provider abstraction
- router/registry
- safety
- security
- SDK
- audit

There are also API surfaces under `backend/api/ai`, `ai_cds`, `ai_clinical`, `ai_copilot`, and `ai_operations`.

Therefore AI is no longer merely a future idea: an architectural subsystem exists. However, the existence of code is **not** evidence that the AI clinical workflow is production-approved. Clinical validation, source governance, safety controls, PHI handling, human oversight and release criteria remain mandatory before clinical use.

## 10. Authentication and security

The project has an explicit authentication freeze document and historical release notes describe production controls including:

- API authentication gates.
- Public registration restricted to patient role.
- Production demo/seed locks.
- JWT-protected file APIs.
- Signed file downloads.
- Security-admin role restrictions.
- Refresh-token revocation handling.
- HSTS in strict environments.

**Rule for new developers:** do not modify authentication/runtime authorization paths casually. Read `docs/AUTH_FREEZE.md` before touching auth, middleware, role checks, token handling or protected route registration.

## 11. Database and migrations

The current backend contains:

- PostgreSQL support.
- Alembic.
- Flask-Migrate.
- `backend/migrations/`.
- Production `DATABASE_URL` configuration.

The Release 2 RC introduced additive migrations `017`, `018`, and `019` for receipt/lab-queue/sample-queue functionality.

Before changing schema:

1. Inspect migration history.
2. Identify the actual production database revision.
3. Confirm backup availability.
4. Apply migrations forward only unless an explicit rollback plan exists.
5. Verify the affected API/UI workflow after migration.

Do not reset production migrations or recreate production tables merely to solve an application error.

## 12. Redis

Redis is an explicit dependency and `REDIS_URL` exists in the production Render blueprint as a synchronized/manual environment value.

A historical deployment issue involved Redis/database tooling displaying `PARAMETER_ORDINAL_POSITION`. This should remain an **open verification item** until the current Render/Railway services and database connections are inspected directly.

Do not infer that Redis is correctly provisioned just because the Python Redis package is installed.

## 13. Render deployment baseline

`backend/render.yaml` currently defines a production web service named `dxcon-api` with:

- Python environment.
- `pip install -r requirements.txt` build.
- Gunicorn start command using `gunicorn.conf.py run:app`.
- Health check `/api/v1/system/health`.
- PostgreSQL database `dxcon-postgres`.
- JSON logging.
- startup DB validation enabled.
- production API auth gate enabled.
- demo mode disabled.
- CORS configured for DxCon domains.
- SMTP variables prepared but several are intentionally manual/sync values.
- `BUILD_VERSION=2.0.0-rc1` in the current blueprint.

**Important:** the blueprint is configuration-as-code, not proof that the Render service is currently deployed and healthy. Verify the live service, latest deployment, environment values and database before declaring production ready.

## 14. Worker and scheduler status

`backend/production_start.py` explicitly supports process roles `api`, `worker`, and `scheduler`.

At the current repository revision, the `worker` and `scheduler` branches are placeholders that print a placeholder message and sleep indefinitely. The file itself states that background jobs must be configured before GA.

Therefore:

- API process: implemented via Gunicorn.
- Worker process: **placeholder / not a real job worker at this entrypoint**.
- Scheduler process: **placeholder / not a real scheduler at this entrypoint**.

This is a critical handover item. Do not tell a new team that background processing is production-complete without verifying the actual deployment architecture and any alternative worker implementation elsewhere in the repository.

## 15. Frontend/mobile surfaces

The repository contains `apps/`, `mobile/`, and `dxcon_patient_app/`. Release documentation also records Flutter Mobile Phase 1 as part of the earlier release scope.

The current handover should therefore treat mobile as an existing codebase/foundation, not as a purely future idea. Exact readiness must be determined from the current build/test configuration for each app.

## 16. Existing documentation

The repository already contains significant project documentation, including:

- `docs/ARCHITECTURE.md`
- `docs/API_OVERVIEW.md`
- `docs/API_REFERENCE.md`
- `docs/AUTH_FREEZE.md`
- `docs/BACKUP.md`
- `docs/BACKUP_RESTORE_RUNBOOK.md`
- `docs/BACKUP_RUNBOOK.md`
- `docs/BARCODE_MODULE.md`
- `docs/BILLING_STATUS.md`
- `docs/CHANGELOG.md`
- `docs/COMPLIANCE_GUIDE.md`
- `docs/CUSTOMER_GUIDE.md`
- Release 1/Release 2 reports and checklists.

The new handover document should complement these documents, not replace them.

## 17. Historical local development notes

Earlier development used a local Flask environment with a SQLite database at `./instance/dxcon.db` and ports 5000/8000. Several port-conflict, import, indentation and JWT-file errors were fixed during early development.

These are historical development notes only. The current production architecture is PostgreSQL + Gunicorn and should not be regressed to the prototype architecture.

## 18. Current status matrix

| Area | Status | Handover interpretation |
|---|---|---|
| Repository | ✅ Active | `main` is the current source tree |
| Backend architecture | ✅ Structured | Flask app factory + modular bootstrap |
| PostgreSQL support | ✅ Present | Production configuration exists |
| Migrations | ✅ Present | Must verify deployed revision before changes |
| Authentication | 🟡 Frozen/protected | Read AUTH_FREEZE before modification |
| Reception M2 | 🟡 RC documented | Historical RC-ready status; verify current main/live deployment |
| Payment | 🟡 Implemented/documented | Fresh regression required before GA |
| Receipt/PDF | 🟡 Implemented/documented | Fresh production verification required |
| Barcode | 🟡 Implemented/documented | Fresh printer/label verification required |
| QR | 🟡 Implemented/documented | Live VNPay settlement was explicitly out of RC scope |
| Laboratory Queue | 🟡 Implemented/documented | Deeper lab workflow remains a separate milestone |
| Sample Queue | 🟡 Implemented/documented | Recent collection fixes are in main history |
| Collector workflow | 🟡 Active development history | Verify end-to-end current-main behavior |
| AI platform | 🟡 Subsystem exists | Clinical production readiness not established by code presence alone |
| Worker | 🔴 Placeholder at production_start.py | Must verify/implement real background jobs |
| Scheduler | 🔴 Placeholder at production_start.py | Must verify/implement real scheduler |
| Redis | 🟡 Configured as dependency | Live service/connectivity must be verified |
| Render | 🟡 IaC present | Live deployment must be verified |
| Railway | 🟡 Historical/backup context | Do not assume it is current production |
| Mobile | 🟡 Foundation/code present | Build and E2E status must be audited |
| IoT/GPS | 🔴 Not established as production workflow | Future/operational milestone |

## 19. Immediate takeover checklist

### P0 — establish truth before coding

- [ ] Confirm current `main` HEAD SHA.
- [ ] Confirm which SHA is deployed on Render.
- [ ] Confirm whether Railway is active, backup, or retired.
- [ ] Confirm production database provider and actual DB URL source without exposing secrets.
- [ ] Confirm current migration revision.
- [ ] Confirm Redis service and connectivity.
- [ ] Confirm `/api/v1/system/health` and readiness endpoints.
- [ ] Confirm Gunicorn process health.
- [ ] Identify all deployed services/processes: API, worker, scheduler, frontend, mobile backend if any.
- [ ] Confirm current environment variables against `.env.production.example` and `render.yaml`.
- [ ] Confirm current CORS domains and production domains.
- [ ] Confirm backup/restore procedure has been tested.

### P1 — regression the business-critical path

Run a clean end-to-end test:

`patient → reception → order → payment → receipt → barcode/QR → collection → collector assignment → lab reception → lab queue → sample queue → result/release`

Record:

- HTTP status.
- Database state.
- UI state.
- Audit trail.
- Queue state.
- Failure/retry behavior.

### P2 — operational completion

- [ ] Replace/verify worker placeholder.
- [ ] Replace/verify scheduler placeholder.
- [ ] Establish retry/idempotency semantics.
- [ ] Establish observability and alerting.
- [ ] Verify backups and restore drills.
- [ ] Verify storage/file lifecycle and signed downloads.
- [ ] Verify payment production boundaries.
- [ ] Verify email/SMTP production configuration.

### P3 — product expansion

- [ ] Complete deeper laboratory workflow.
- [ ] Complete collector/mobile workflow.
- [ ] Doctor workflow.
- [ ] Live payment settlement where legally/operationally approved.
- [ ] GPS/dispatch/IoT.
- [ ] AI clinical workflow with validated governance and human oversight.

## 20. Rules for the next developer

1. **Do not rewrite the architecture before auditing it.**
2. **Do not use old chat history as the source of truth when the repository contains newer code.**
3. **Do not modify authentication without reading `docs/AUTH_FREEZE.md`.**
4. **Do not reset production migrations.**
5. **Do not claim production readiness from a passing historical release report.**
6. **Do not expose secrets in commits, tickets, logs or handover documents.**
7. **Use additive, reviewable changes and named commits/PRs for release work.**
8. **For workflow bugs, test the full state transition, not just the failing HTTP endpoint.**
9. **Treat AI clinical output as a safety-critical subsystem, not ordinary chatbot text generation.**
10. **Before changing deployment, capture the current deployed SHA, migration revision and backup status.**

## 21. Recommended next milestone

The best next milestone is **DxCon Production Baseline Verification**, not a new feature.

Definition of done:

1. Current `main` SHA documented.
2. Live Render/production SHA documented.
3. Database and migration revision documented.
4. Redis verified.
5. API health/readiness verified.
6. Worker/scheduler architecture verified.
7. Backup and restore verified.
8. Reception → Collector → Laboratory workflow passes end-to-end.
9. Auth freeze remains intact.
10. Only after the above is complete should the next feature sprint begin.

## 22. Source-of-truth hierarchy

When information conflicts, use this order:

1. **Live production state and logs** — for runtime truth.
2. **Current `main` repository code** — for source-code truth.
3. **Current migrations/database revision** — for schema truth.
4. **Current deployment manifests** — for intended deployment configuration.
5. **Release reports/checklists** — for historical verification evidence.
6. **Old chat/project notes** — for product intent and development history only.

---

**Handover conclusion:** DxCon is already a substantial multi-module platform. The main risk is no longer “there is no code”; the main risk is **configuration/state drift between source, migrations, deployment, Redis, background processes and documented release status**. The next developer should therefore begin with verification and controlled stabilization, then continue feature development from the existing architecture.
