# DxCon Platform — Engineering Backlog

**Created:** 2026-06-26  
**Source:** [`REPOSITORY_ASSESSMENT.md`](REPOSITORY_ASSESSMENT.md)  
**Production readiness baseline:** 44 / 100  
**Branch context:** `feature/collector-lab-workflow` (FP-003 partially delivered)

This backlog prioritizes work required to move DxCon from **demo/staging** to a **production-grade medical logistics platform**. Items are grouped P0–P3. **Recommended implementation order** is global across all priorities — complete P0 in order before starting P1 unless noted as parallel-safe.

---

## Summary

| Priority | Label | Items | Theme |
|---|---|---|---|
| **P0** | Must fix before production | 10 | Security, schema, compliance gates |
| **P1** | High priority | 12 | Architecture, chain-of-custody, CI, FP-003 |
| **P2** | Medium priority | 12 | Consolidation, performance, developer experience |
| **P3** | Nice to have | 10 | UX polish, optimization, long-term cleanup |

---

## P0 — Must Fix Before Production

> **Gate:** No production deployment handling real patient data or specimens until all P0 items are closed.

---

### BL-P0-001 — Authenticate logistics, collector, and shipment APIs

| Field | Detail |
|---|---|
| **Problem** | Chain-of-custody endpoints (`/api/v1/collector/*`, `/api/v1/shipments/*`, `/api/v1/logistics-v2/*`, `/api/v1/transport-boxes/*`, QR scan/receive) accept unauthenticated requests. |
| **Risk** | Unauthorized actors can accept shipments, start trips, receive specimens, or alter transport box state — direct patient safety and regulatory violation. |
| **Effort** | **M** |
| **Impact** | **Critical** — closes the largest security gap in the platform. |
| **Recommended implementation order** | **1** |

**Implementation notes:** Extend JWT + role decorators (`COLLECTOR`, `LAB`, `LOGISTICS`, `SUPER_ADMIN`); preserve backward-compatible optional auth period only in staging with feature flag.

---

### BL-P0-002 — Block privileged role self-registration

| Field | Detail |
|---|---|
| **Problem** | `POST /api/v1/auth/register` accepts any `role`, including `SUPER_ADMIN`, `DOCTOR`, and `COLLECTOR`. |
| **Risk** | Full platform compromise via public registration; privilege escalation without audit trail. |
| **Effort** | **S** |
| **Impact** | **Critical** — eliminates trivial admin takeover vector. |
| **Recommended implementation order** | **2** (can run parallel with BL-P0-001) |

**Implementation notes:** Default register to `PATIENT` only; privileged roles assigned via `/api/v1/security/users` by admin.

---

### BL-P0-003 — Remove hardcoded secrets; enforce environment-only configuration

| Field | Detail |
|---|---|
| **Problem** | `app.secret_key = "dxcon-secret-key"` hardcoded in `__init__.py`; dev fallbacks in `config.py` for `SECRET_KEY` and `JWT_SECRET_KEY`. |
| **Risk** | Session forgery, JWT tampering, credential exposure if defaults reach production. |
| **Effort** | **S** |
| **Impact** | **Critical** — baseline production security hygiene. |
| **Recommended implementation order** | **3** |

**Implementation notes:** Fail fast on boot if secrets missing in `APP_ENV=production`; use Render-generated env vars per `render.yaml`.

---

### BL-P0-004 — Introduce Alembic migrations; disable `db.create_all()` in production

| Field | Detail |
|---|---|
| **Problem** | Schema managed via `db.create_all()` at startup; Alembic/Flask-Migrate in requirements but not configured; install scripts embed duplicate model definitions. |
| **Risk** | Irreversible schema drift, failed deploys, data loss on rollback; no audit trail of schema changes. |
| **Effort** | **M** |
| **Impact** | **Critical** — required for safe PostgreSQL evolution on Render. |
| **Recommended implementation order** | **4** |

**Implementation notes:** Initial migration from current models; gate production boot on `flask db upgrade`; keep `create_all()` dev-only.

---

### BL-P0-005 — Disable or protect demo seed endpoints in production

| Field | Detail |
|---|---|
| **Problem** | `POST /api/v1/seeds/demo-operations` can mutate production data if exposed. |
| **Risk** | Data corruption, PHI contamination, demo patients/orders in live environment. |
| **Effort** | **S** |
| **Impact** | **High** — prevents catastrophic ops mistakes. |
| **Recommended implementation order** | **5** |

**Implementation notes:** Return 403 when `APP_ENV=production` or require admin JWT + explicit feature flag.

---

### BL-P0-006 — Remove plaintext password fallback in web authentication

| Field | Detail |
|---|---|
| **Problem** | `web/auth.py` `verify_password()` accepts direct string equality before bcrypt check. |
| **Risk** | Weak or legacy plaintext credentials remain valid; undermines bcrypt migration. |
| **Effort** | **S** |
| **Impact** | **High** — credential integrity for web portal users. |
| **Recommended implementation order** | **6** |

**Implementation notes:** Run `migrate_passwords.py` if needed; remove plaintext branch after migration confirmed.

---

### BL-P0-007 — Apply consistent authentication guards on web admin routes

| Field | Detail |
|---|---|
| **Problem** | `@role_required` applied selectively; many of 93 web routes (shipments, logistics, ops, finance) lack session guards. |
| **Risk** | Unauthenticated browser access to PHI, shipment controls, and financial data. |
| **Effort** | **M** |
| **Impact** | **High** — closes web-side equivalent of open API problem. |
| **Recommended implementation order** | **7** |

**Implementation notes:** Audit all web blueprints; apply `login_required` / `role_required` by route group; add web route auth tests.

---

### BL-P0-008 — Restrict CORS to known origins

| Field | Detail |
|---|---|
| **Problem** | `CORS(app)` enabled globally without origin whitelist. |
| **Risk** | Cross-origin abuse of authenticated browser sessions; increased CSRF surface. |
| **Effort** | **S** |
| **Impact** | **High** — standard production API hardening. |
| **Recommended implementation order** | **8** |

**Implementation notes:** Allow Render app URL, local dev origins, Flutter web origins; deny `*` in production.

---

### BL-P0-009 — Run unit tests in CI as merge gate

| Field | Detail |
|---|---|
| **Problem** | GitHub Actions runs py_compile on 2 files only; `backend/tests/` never executed in CI. |
| **Risk** | Regressions ship to `main` undetected; FP-003 and future changes unprotected. |
| **Effort** | **S** |
| **Impact** | **High** — minimum quality gate before production. |
| **Recommended implementation order** | **9** |

**Implementation notes:** Add `python -m unittest discover -s tests -p 'test_*.py'` to workflow; expand compile to all `app/` modules.

---

### BL-P0-010 — Authenticate QR scan and lab-receive endpoints

| Field | Detail |
|---|---|
| **Problem** | QR scan (`/api/v1/logistics-v2/scan`, `/api/v1/shipments/scan/*`, `/receive-by-box/*`) and lab receive paths are open. |
| **Risk** | Spurious lab receive events; chain-of-custody records falsified without actor identity. |
| **Effort** | **M** |
| **Impact** | **Critical** — compliance integrity at handoff points. |
| **Recommended implementation order** | **10** |

**Implementation notes:** Pair with BL-P0-001; lab role required for receive; scan may require collector or lab JWT.

---

## P1 — High Priority

> **Target:** Complete after P0 gate. Required for staging sign-off and FP-003 production release.

---

### BL-P1-001 — Complete FP-003 (Flutter commit, docs, verify script, idempotent service)

| Field | Detail |
|---|---|
| **Problem** | FP-003 Commits 1–2 done; Flutter (`mobile/`) untracked; Commit 4 (docs + `verify_collector_workflow_v1.py`) not started; service not idempotent. |
| **Risk** | Collector workflow incomplete in VCS; mobile field ops unreproducible; duplicate audit logs on retry. |
| **Effort** | **M** |
| **Impact** | **High** — finishes in-flight critical logistics feature. |
| **Recommended implementation order** | **11** |

**Implementation notes:** Commits 3–4 per approved plan; refactor `collector_workflow` for idempotency; update `LOGISTICS_CHAIN_OF_CUSTODY.md` with `ACCEPTED` status.

---

### BL-P1-002 — Unified compliance logger (audit + timeline + event in one transaction)

| Field | Detail |
|---|---|
| **Problem** | Compliance writes split across `write_audit`, manual `ShipmentTimeline`, and `write_event`; not all state transitions use all three. |
| **Risk** | Incomplete chain-of-custody evidence; audit gaps during incidents or regulatory review. |
| **Effort** | **M** |
| **Impact** | **High** — aligns runtime with documented architecture rules. |
| **Recommended implementation order** | **12** |

**Implementation notes:** Create `ComplianceLogger.record(shipment, event_type, ...)`; migrate FP-003 service first, then lab receive and arrived transitions.

---

### BL-P1-003 — Lab receive service with full compliance logging

| Field | Detail |
|---|---|
| **Problem** | Lab receive implemented in three places (API receive, web receive, receive-by-box) with audit-only side effects; no shared service. |
| **Risk** | Inconsistent receive behavior; missing timeline/events; box status updates differ by path. |
| **Effort** | **L** |
| **Impact** | **High** — core handoff in diagnostic chain. |
| **Recommended implementation order** | **13** |

**Implementation notes:** Single `LabReceiveService`; thin routes; capture receiver, timestamp, note, temperature, GPS placeholder.

---

### BL-P1-004 — Shipment `ARRIVED` transition compliance logging

| Field | Detail |
|---|---|
| **Problem** | `/api/v1/shipments/<id>/arrived` writes audit only — no timeline or event log. |
| **Risk** | Gap in chain-of-custody between `IN_TRANSIT` and `RECEIVED`. |
| **Effort** | **S** |
| **Impact** | **High** — completes shipment state audit trail. |
| **Recommended implementation order** | **14** |

**Implementation notes:** Delegate to shipment service via compliance logger (BL-P1-002).

---

### BL-P1-005 — Extract business logic into service classes

| Field | Detail |
|---|---|
| **Problem** | 86 route/web modules contain DB mutations; only 11 services exist; FP-003 is the sole logistics service pattern. |
| **Risk** | Untestable logic; duplicated queries; inconsistent validation; high regression cost. |
| **Effort** | **L** |
| **Impact** | **High** — foundational architecture improvement. |
| **Recommended implementation order** | **15** |

**Implementation notes:** Phased: (1) shipment, (2) sample/booking, (3) lab receive, (4) finance; routes validate → call service → respond.

---

### BL-P1-006 — Consolidate workflow and collector APIs behind shared services

| Field | Detail |
|---|---|
| **Problem** | Parallel paths: `/api/v1/workflow/*` vs `/api/v1/collector/*` for checkin, collected, sample status; duplicate sample code generators. |
| **Risk** | Behavioral drift; one path updated, other broken; collector mobile vs web inconsistency. |
| **Effort** | **L** |
| **Impact** | **High** — reduces duplicate modules (assessment item #4, #12). |
| **Recommended implementation order** | **16** |

**Implementation notes:** Introduce `BookingWorkflowService` and `SampleWorkflowService`; deprecate duplicate endpoints with backward-compatible wrappers.

---

### BL-P1-007 — Add pagination and query limits to list endpoints

| Field | Detail |
|---|---|
| **Problem** | List APIs (`/patients`, `/shipments`, `/collector/shipments`, etc.) return unbounded result sets. |
| **Risk** | Memory exhaustion, slow responses, DoS via large payloads; dashboard N+1 amplification. |
| **Effort** | **M** |
| **Impact** | **High** — production stability under load. |
| **Recommended implementation order** | **17** |

**Implementation notes:** Standard `?page=&limit=` contract; default limit 50; document in API summary.

---

### BL-P1-008 — Rate limit authentication endpoints

| Field | Detail |
|---|---|
| **Problem** | No throttling on `/api/v1/auth/login`, `/register`, or web `/login`. |
| **Risk** | Brute-force credential attacks; registration spam. |
| **Effort** | **S** |
| **Impact** | **Medium–High** — standard auth hardening. |
| **Recommended implementation order** | **18** |

**Implementation notes:** Flask-Limiter or reverse-proxy rate limits on Render; log lockout events to audit.

---

### BL-P1-009 — Authenticate AI and clinical result endpoints

| Field | Detail |
|---|---|
| **Problem** | AI interpret/analyze endpoints and test result APIs lack consistent JWT/role enforcement. |
| **Risk** | Unauthorized access to clinical interpretations and PHI-adjacent data. |
| **Effort** | **M** |
| **Impact** | **High** — clinical data protection. |
| **Recommended implementation order** | **19** |

**Implementation notes:** Doctor/Lab roles for AI generation; patient JWT scoped to own orders/results.

---

### BL-P1-010 — Enforce doctor approval gate before patient result visibility

| Field | Detail |
|---|---|
| **Problem** | Doctor approval exists in web portal (`/doctor/approve/<result_id>`) but not enforced at API level for patient mobile/portal routes. |
| **Risk** | Unapproved results visible to patients; clinical liability. |
| **Effort** | **M** |
| **Impact** | **High** — medical workflow integrity. |
| **Recommended implementation order** | **20** |

**Implementation notes:** Add `approved_at` / `approved_by` checks in patient result APIs; service-layer gate.

---

### BL-P1-011 — Add Flutter CI and commit staff mobile app

| Field | Detail |
|---|---|
| **Problem** | `mobile/dxcon_mobile` untracked; no Flutter workflow; placeholder screens untested. |
| **Risk** | Mobile releases not reproducible; FP-003 collector UI lost between environments. |
| **Effort** | **M** |
| **Impact** | **High** — mobile delivery pipeline. |
| **Recommended implementation order** | **21** |

**Implementation notes:** GitHub Actions: `flutter analyze`, `flutter test`; environment config via `--dart-define`.

---

### BL-P1-012 — Remove or relocate `backend/super_admin` default credential recipe

| Field | Detail |
|---|---|
| **Problem** | Repo contains curl recipe registering `admin@dxcon.vn` with password `123456`. |
| **Risk** | Credential stuffing; operators deploy with known defaults. |
| **Effort** | **S** |
| **Impact** | **Medium** — security hygiene and audit finding remediation. |
| **Recommended implementation order** | **22** |

**Implementation notes:** Move to secure internal runbook; use one-time bootstrap script with forced password change.

---

## P2 — Medium Priority

> **Target:** Staging hardening and maintainability after P0/P1 core path is stable.

---

### BL-P2-001 — Consolidate AI APIs to single versioned surface

| Field | Detail |
|---|---|
| **Problem** | Three AI paths: `/api/v1/ai`, `/api/v2/ai`, `/api/v1/ai-v2` with duplicated interpret logic inline and in services. |
| **Risk** | Inconsistent clinical interpretations; maintenance burden; client confusion. |
| **Effort** | **M** |
| **Impact** | **Medium** — reduces duplicate modules (assessment #9). |
| **Recommended implementation order** | **23** |

**Implementation notes:** Canonical `/api/v1/ai/*`; deprecate v2 paths with sunset headers; centralize in `ai_interpretation` service.

---

### BL-P2-002 — Unify patient mobile API (`/mobile` vs `/patient`)

| Field | Detail |
|---|---|
| **Problem** | Overlapping patient endpoints in `mobile/routes.py` and `patient_mobile/routes.py`; separate mobile login path. |
| **Risk** | Client fragmentation; duplicate bug fixes; inconsistent JWT behavior. |
| **Effort** | **M** |
| **Impact** | **Medium** — simplifies Flutter/patient clients. |
| **Recommended implementation order** | **24** |

**Implementation notes:** Single `/api/v1/patient/*` surface; backward-compatible aliases during transition.

---

### BL-P2-003 — Unified QR scan and resolve service

| Field | Detail |
|---|---|
| **Problem** | QR logic split across `logistics_v2/scan`, `shipments/scan`, `box_qr`; inconsistent event logging on scan. |
| **Risk** | Scan events missing from audit trail; duplicate lookup code. |
| **Effort** | **M** |
| **Impact** | **Medium** — chain-of-custody completeness at scan points. |
| **Recommended implementation order** | **25** |

**Implementation notes:** `QrScanService.resolve(payload)` + optional `ComplianceLogger` on scan actions.

---

### BL-P2-004 — Resolve duplicate web URL registrations

| Field | Detail |
|---|---|
| **Problem** | `GET /collector`, `/dispatch`, `/executive` each registered by two blueprints (allowlisted in CI, ambiguous at runtime). |
| **Risk** | Non-deterministic handler selection; wrong UI served after deploy. |
| **Effort** | **S** |
| **Impact** | **Medium** — routing predictability. |
| **Recommended implementation order** | **26** |

**Implementation notes:** Merge or rename legacy routes; remove CI allowlist entries once fixed.

---

### BL-P2-005 — Clean up orphan and duplicate modules

| Field | Detail |
|---|---|
| **Problem** | Orphans: `backend/app.py`, `users_bp` (unregistered), `HomeSampling` model, `api/mobile/home_collection.py`; duplicate `alerts_bp` registration; 8 `.save` backup files. |
| **Risk** | Developer confusion; accidental use of dead code paths; repo noise. |
| **Effort** | **S** |
| **Impact** | **Low–Medium** — codebase clarity. |
| **Recommended implementation order** | **27** |

**Implementation notes:** Delete or register each orphan explicitly; document decision for `HomeSampling` (integrate vs deprecate).

---

### BL-P2-006 — Replace install scripts with migrations and feature flags

| Field | Detail |
|---|---|
| **Problem** | Six install scripts re-embed model and route source instead of importing application modules. |
| **Risk** | Script drift from live code; failed installs; duplicate definitions. |
| **Effort** | **M** |
| **Impact** | **Medium** — ops reliability after BL-P0-004. |
| **Recommended implementation order** | **28** |

**Implementation notes:** Retire `install_*.py` after Alembic baseline; use seeds only in non-production.

---

### BL-P2-007 — Fix N+1 queries in web dashboards

| Field | Detail |
|---|---|
| **Problem** | Dashboard and portal pages loop collections with per-row DB lookups (patients, orders, samples). |
| **Risk** | Slow page loads under real data volume; DB connection pressure. |
| **Effort** | **M** |
| **Impact** | **Medium** — ops UX at scale. |
| **Recommended implementation order** | **29** |

**Implementation notes:** Batch queries or joined loads; prioritize `/dashboard`, `/monitor`, `/executive-v9`.

---

### BL-P2-008 — Add staging environment configuration

| Field | Detail |
|---|---|
| **Problem** | Single production Render target; Flutter hardcodes production URL; patient app uses `127.0.0.1`. |
| **Risk** | Testing against production; config mistakes during release. |
| **Effort** | **M** |
| **Impact** | **Medium** — safe release pipeline. |
| **Recommended implementation order** | **30** |

**Implementation notes:** Render staging service + `APP_ENV=staging`; Flutter `--dart-define=API_BASE=...`.

---

### BL-P2-009 — Add root README and `.env.example`

| Field | Detail |
|---|---|
| **Problem** | No project README; `.env` gitignored without documented template. |
| **Risk** | Slow onboarding; misconfigured local/prod environments. |
| **Effort** | **S** |
| **Impact** | **Medium** — team velocity and ops consistency. |
| **Recommended implementation order** | **31** |

**Implementation notes:** Document backend, mobile, Render deploy, required env vars, test commands.

---

### BL-P2-010 — Expand backend test coverage for auth and logistics

| Field | Detail |
|---|---|
| **Problem** | ~4% API coverage; zero auth/security tests; logistics beyond FP-003 untested. |
| **Risk** | P0/P1 fixes regress without detection. |
| **Effort** | **L** |
| **Impact** | **Medium–High** — sustained quality after CI gate (BL-P0-009). |
| **Recommended implementation order** | **32** |

**Implementation notes:** Target: auth register/login, JWT guards, lab receive, QR scan, workflow service; one test per new API change policy.

---

### BL-P2-011 — Consolidate collector web portals

| Field | Detail |
|---|---|
| **Problem** | Three collector UIs: `collector_portal`, `collector_console`, `collector_mobile` with overlapping job/shipment actions. |
| **Risk** | UX fragmentation; triple maintenance for field ops features. |
| **Effort** | **M** |
| **Impact** | **Medium** — operator experience. |
| **Recommended implementation order** | **33** |

**Implementation notes:** Single `/collector-mobile` as primary; redirect legacy URLs.

---

### BL-P2-012 — Input validation layer for API payloads

| Field | Detail |
|---|---|
| **Problem** | Marshmallow in requirements but unused; routes accept raw `request.json` without schema validation. |
| **Risk** | Invalid state transitions, type errors, unexpected 500s; harder to document contracts. |
| **Effort** | **M** |
| **Impact** | **Medium** — API reliability and security. |
| **Recommended implementation order** | **34** |

**Implementation notes:** Schemas per blueprint for POST/PATCH bodies; validate before service calls.

---

## P3 — Nice to Have

> **Target:** Post-production optimization and long-term platform maturity.

---

### BL-P3-001 — Merge Flutter apps or shared API client package

| Field | Detail |
|---|---|
| **Problem** | `dxcon_mobile` (staff) and `dxcon_patient_app` (patient web) are separate with duplicated HTTP patterns. |
| **Risk** | Duplicated mobile maintenance; inconsistent API usage. |
| **Effort** | **L** |
| **Impact** | **Medium** (long-term) — mobile architecture simplification. |
| **Recommended implementation order** | **35** |

**Implementation notes:** Monorepo package `dxcon_api_client` or single app with role-based routing.

---

### BL-P3-002 — Photo evidence capture on lab receive

| Field | Detail |
|---|---|
| **Problem** | Architecture doc specifies photo evidence at lab receive; API does not enforce or store photos. |
| **Risk** | Regulatory evidence gap for disputed handoffs. |
| **Effort** | **L** |
| **Impact** | **Low–Medium** — compliance enhancement beyond MVP. |
| **Recommended implementation order** | **36** |

**Implementation notes:** Extend `ResultFile` or new `ShipmentEvidence` model; mobile/web upload flow.

---

### BL-P3-003 — Integrate or deprecate `HomeSampling` model

| Field | Detail |
|---|---|
| **Problem** | `home_sampling_requests` table/model exists but is unregistered and has no API — overlaps `HomeCollection`. |
| **Risk** | Dead schema; future confusion about booking source of truth. |
| **Effort** | **S** |
| **Impact** | **Low** — schema clarity. |
| **Recommended implementation order** | **37** |

**Implementation notes:** Prefer extending `HomeCollection`; drop orphan table via migration if unused.

---

### BL-P3-004 — Consolidate executive dashboards (v8/v9/legacy)

| Field | Detail |
|---|---|
| **Problem** | Three executive modules (`executive.py`, `executive_v8.py`, `executive_v9.py`); duplicate `/executive` URL. |
| **Risk** | Stakeholders see inconsistent KPIs; maintenance overhead. |
| **Effort** | **M** |
| **Impact** | **Low–Medium** — executive UX. |
| **Recommended implementation order** | **38** |

**Implementation notes:** Standardize on `/executive-v9`; redirect legacy paths.

---

### BL-P3-005 — Add caching for dashboard statistics

| Field | Detail |
|---|---|
| **Problem** | Dashboard and system stats recomputed on every request; no Redis/in-memory cache. |
| **Risk** | DB load under concurrent admin users. |
| **Effort** | **M** |
| **Impact** | **Low–Medium** — performance at scale. |
| **Recommended implementation order** | **39** |

**Implementation notes:** Short TTL cache for `/api/v1/dashboard/summary`, `/system/stats`.

---

### BL-P3-006 — Background job queue for AI batch and heavy ops

| Field | Detail |
|---|---|
| **Problem** | `ai-v2/generate-all` and seed operations run synchronously in request thread. |
| **Risk** | Request timeouts; poor UX on large order sets. |
| **Effort** | **L** |
| **Impact** | **Low–Medium** — scalability for AI batch features. |
| **Recommended implementation order** | **40** |

**Implementation notes:** Celery/RQ or Render background workers; job status API.

---

### BL-P3-007 — Web UI template layer and i18n foundation

| Field | Detail |
|---|---|
| **Problem** | 50 web modules use inline f-string HTML; mixed Vietnamese/English strings. |
| **Risk** | Untestable UI; hard localization; XSS risk if user input ever injected unsafely. |
| **Effort** | **L** |
| **Impact** | **Low–Medium** — maintainability and enterprise UX. |
| **Recommended implementation order** | **41** |

**Implementation notes:** Jinja2 templates incrementally; extract strings for future i18n.

---

### BL-P3-008 — Wire Flutter placeholder screens (orders, files, profile)

| Field | Detail |
|---|---|
| **Problem** | `OrdersScreen`, `FilesScreen` are placeholders; no API integration. |
| **Effort** | **M** |
| **Impact** | **Low–Medium** — staff app completeness. |
| **Recommended implementation order** | **42** |

**Implementation notes:** After BL-P2-002 patient API unification; reuse auth token from login.

---

### BL-P3-009 — SQLAlchemy relationship definitions and FK constraints

| Field | Detail |
|---|---|
| **Problem** | Models use string ID columns without `relationship()` or DB-level foreign keys. |
| **Risk** | Orphan records; no referential integrity; harder ORM queries. |
| **Effort** | **L** |
| **Impact** | **Low–Medium** — data integrity long-term. |
| **Recommended implementation order** | **43** |

**Implementation notes:** Phased migration adding FKs nullable first; add relationships for hot paths (Order → Patient).

---

### BL-P3-010 — Connection pool and query timeout tuning

| Field | Detail |
|---|---|
| **Problem** | Default SQLAlchemy pool settings; no documented query timeouts. |
| **Risk** | Connection exhaustion under spike load on Render. |
| **Effort** | **S** |
| **Impact** | **Low** — ops tuning. |
| **Recommended implementation order** | **44** |

**Implementation notes:** Configure `SQLALCHEMY_ENGINE_OPTIONS` for production; monitor via Render metrics.

---

## Recommended Execution Phases

| Phase | Order range | Goal | Exit criteria |
|---|---|---|---|
| **Phase 0 — Production gate** | BL-P0-001 → BL-P0-010 | Security + schema + CI | All P0 closed; staging pen-test pass |
| **Phase 1 — Chain of custody** | BL-P1-001 → BL-P1-012 | FP-003 + compliance services | Collector/lab workflows fully logged and tested |
| **Phase 2 — Platform hardening** | BL-P2-001 → BL-P2-012 | Consolidation + DX + tests | Readiness score ≥ 60 |
| **Phase 3 — Maturity** | BL-P3-001 → BL-P3-010 | Optimization + UX | Readiness score ≥ 75 |

---

## Traceability to Repository Assessment

| Assessment section | Backlog coverage |
|---|---|
| Security concerns (#17) | BL-P0-001–010, BL-P1-008–012, BL-P0-006 |
| Technical debt (#14) | BL-P1-005–006, BL-P2-005–006, BL-P3-007 |
| Duplicate modules (#15) | BL-P1-006, BL-P2-001–004, BL-P2-011, BL-P3-004 |
| Missing features (#16) | BL-P0-004, BL-P1-001–004, BL-P2-008–009, BL-P3-002 |
| Test coverage (#12) | BL-P0-009, BL-P2-010, BL-P1-011 |
| CI/CD (#13) | BL-P0-009, BL-P1-011 |
| Performance (#18) | BL-P1-007, BL-P2-007, BL-P3-005–006, BL-P3-010 |
| Top 20 recommendations (#20) | Mapped to BL-P0 through BL-P2 items |

---

## Effort Legend

| Size | Typical duration (1 engineer) |
|---|---|
| **S** | ≤ 1 day |
| **M** | 2–5 days |
| **L** | 1–3 weeks |

---

*Backlog derived from [`REPOSITORY_ASSESSMENT.md`](REPOSITORY_ASSESSMENT.md). No application code was modified.*
