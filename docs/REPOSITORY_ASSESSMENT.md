# DxCon Platform — Repository Assessment Report

**Report date:** 2026-06-26  
**Assessor role:** Lead Software Engineer  
**Repository:** `dxcon-platform`  
**Branch analyzed:** `feature/collector-lab-workflow` (2 FP-003 commits ahead of `main`)  
**Method:** Read-only static analysis of source, routes, config, CI, and deployment artifacts

---

## Executive Summary

DxCon is an enterprise diagnostic logistics platform implemented as a **monolithic Flask application** with **124 REST endpoints**, **93 web routes**, **30 registered SQLAlchemy models**, and **two Flutter codebases**. The platform spans the full diagnostic chain: patient booking, field collection, cold-chain transport, lab processing, AI-assisted interpretation, doctor approval, billing, and executive reporting.

The codebase is **feature-rich but architecturally immature** for a production medical platform. Compliance primitives (audit logs, shipment timelines, event logs, QR chain-of-custody) exist, yet business logic is concentrated in route handlers, test coverage is minimal, schema management is ad hoc, and several security controls are missing or inconsistent.

**Production readiness score: 44 / 100**

---

## 1. Project Structure

```
dxcon-platform/
├── backend/                    # Flask API + web UI (primary system)
│   ├── app/
│   │   ├── api/               # 36 REST blueprint modules
│   │   ├── web/               # 50 server-rendered HTML modules
│   │   ├── services/          # 11 business-logic modules
│   │   ├── models/            # 31 SQLAlchemy model files
│   │   ├── core/              # Config, auth, audit, events, QR, statuses
│   │   ├── extensions/        # db, jwt
│   │   └── utils/             # Session auth helpers
│   ├── scripts/               # 16 ops/verification/install scripts
│   ├── tests/                 # 1 test module (5 cases)
│   ├── render.yaml            # Render deployment spec
│   ├── requirements.txt       # Python 3.9 dependencies
│   ├── run.py                 # Production entry (gunicorn target)
│   └── app.py                 # Legacy orphaned prototype
├── mobile/dxcon_mobile/       # Staff Flutter app (untracked in git)
├── dxcon_patient_app/         # Patient Flutter/web prototype
├── docs/                      # Architecture + recovery docs
└── .github/workflows/         # Backend CI (1 workflow)
```

| Layer | Files (approx) | Maturity |
|---|---|---|
| Backend Python | ~146 under `backend/app/` | High feature count, low separation |
| Flutter staff | 12 Dart source files | Early stage; FP-003 WIP |
| Flutter patient | 2 Dart source files | Web prototype |
| Documentation | 2 architecture docs + this report | Thin |
| Tests | 1 meaningful backend module | Critical gap |

**Git state:** `mobile/` directory exists on disk but is **untracked**. FP-003 Commits 1–2 are committed; Commits 3–4 are incomplete.

---

## 2. Backend Architecture

### 2.1 Pattern

- **Factory app:** `backend/app/__init__.py` → `create_app()`
- **Persistence:** Flask-SQLAlchemy 3.x + PostgreSQL (production) / SQLite (dev)
- **Auth:** Dual system — Flask sessions (web) + JWT (mobile/API)
- **Rendering:** Inline HTML f-strings in web blueprints (no template directory)
- **Schema:** `db.create_all()` at startup; no Alembic migration folder despite dependencies

### 2.2 Layering assessment

| Layer | Intended role | Actual state |
|---|---|---|
| Routes (`api/`, `web/`) | Thin HTTP adapters | **Heavy** — most contain business logic + DB commits |
| Services (`services/`) | Business rules | **Underused** — 11 services vs 86 route modules |
| Core (`core/`) | Cross-cutting utilities | Good — audit, events, QR, statuses |
| Models (`models/`) | Data + serialization | Good — `to_dict()` pattern; no ORM relationships |

### 2.3 Architectural strengths

- Blueprint modularization by domain
- Centralized audit/event helpers (`write_audit`, `write_event`)
- FP-003 `collector_workflow` service demonstrates target pattern
- Compliance tables (`audit_logs`, `shipment_timelines`, `event_logs`)
- Environment-driven config via `python-dotenv`

### 2.4 Architectural weaknesses

- No repository/query layer — duplicated lookups across modules
- No formal migration pipeline
- Legacy `backend/app.py` coexists with factory app
- Install scripts re-embed model/route source instead of importing modules
- Global CORS without origin restrictions

---

## 3. Flask Blueprints

**Total registered blueprints:** 87 (`register_blueprint` calls in `__init__.py`)

### 3.1 API blueprints (registered)

| Blueprint | Prefix | Module |
|---|---|---|
| `auth_bp` | `/api/v1/auth` | Login, register |
| `admin_bp` | `/api/v1/admin` | Admin users |
| `admin_security_bp` | `/api/v1/admin-security` | Secure health |
| `patients_bp` | `/api/v1/patients` | Patient CRUD |
| `laboratories_bp` | `/api/v1/laboratories` | Lab CRUD |
| `test_catalogs_bp` | `/api/v1/test-catalogs` | Test catalog |
| `orders_bp` | `/api/v1/orders` | Orders |
| `order_items_bp` | `/api/v1/order-items` | Order items |
| `sample_collections_bp` | `/api/v1/sample-collections` | Sample collections |
| `test_results_bp` | `/api/v1/test-results` | Test results |
| `companies_bp` | `/api/v1/companies` | B2B companies |
| `contracts_bp` | `/api/v1/contracts` | Contracts |
| `contract_prices_bp` | `/api/v1/contract-prices` | Pricing |
| `invoices_bp` | `/api/v1/invoices` | Invoicing |
| `payments_bp` | `/api/v1/payments` | Payments |
| `dashboard_bp` | `/api/v1/dashboard` | Dashboard summary |
| `seeds_bp` | `/api/v1/seeds` | Demo seeding |
| `mobile_bp` | `/api/v1/mobile` | Patient mobile |
| `patient_mobile_bp` | `/api/v1/patient` | Patient portal API |
| `workflow_bp` | `/api/v1/workflow` | Home collection workflow |
| `collector_bp` | `/api/v1/collector` | Collector + FP-003 shipments |
| `home_collections_bp` | `/api/v1/home-collections` | Home collections |
| `sample_trackings_bp` | `/api/v1/sample-trackings` | Sample tracking |
| `incidents_bp` | `/api/v1/incidents` | Incidents |
| `alerts_bp` | `/api/v1/alerts` | Alerts (registered twice) |
| `shipments_bp` | `/api/v1/shipments` | Shipment lifecycle |
| `logistics_v2_bp` | `/api/v1/logistics-v2` | Logistics v2 |
| `transport_boxes_bp` | `/api/v1/transport-boxes` | Transport boxes |
| `box_qr_bp` | `/api/v1/box-qr` | Box QR payloads |
| `result_files_bp` | `/api/v1/result-files` | Result file delivery |
| `system_bp` | `/api/v1/system` | Health, stats, routes |
| `ops_bp` | `/api/v1/ops` | Ops health, production check |
| `security_api_bp` | `/api/v1/security` | User/role admin |
| `ai_bp` | `/api/v1/ai` | AI interpret v1 |
| `ai_v2_bp` | `/api/v2/ai` | AI analyze order v2 |
| `ai_interpret_v2_bp` | `/api/v1/ai-v2` | AI interpret v2 |
| `ai_batch_bp` | `/api/v1/ai-v2` | AI batch generate |

### 3.2 Web blueprints (50 modules)

Auth, dashboard, clinical CRUD, patient/doctor portals, collector tools, logistics, dispatch, lab worklist, executive/finance/CRM dashboards, ops monitoring, audit center, security admin, result upload/verify, analytics/KPI pages.

### 3.3 Unregistered / orphan blueprints

| Module | Issue |
|---|---|
| `api/users/routes.py` | `users_bp` never registered |
| `api/mobile/home_collection.py` | Separate blueprint never registered |

### 3.4 Duplicate URL registrations

| URL | Competing handlers |
|---|---|
| `GET /collector` | `collector_portal_web`, `collector_console_web` |
| `GET /dispatch` | `dispatch_web`, `logistics_web` |
| `GET /executive` | `executive_web`, `executive_v8` |

These are allowlisted in `check_routes.py` but remain runtime ambiguities.

### 3.5 `__init__.py` hygiene issues

- `alerts_bp` imported and registered **twice**
- `Alert` imported twice in `models/__init__.py`
- Hardcoded `app.secret_key = "dxcon-secret-key"` overrides env-based secrets

---

## 4. Database Models and Relationships

### 4.1 ORM style

Models use **UUID string primary keys** and **logical foreign keys** (`patient_id`, `collector_id`, etc.) stored as plain `String(36)` columns. There are **no SQLAlchemy `relationship()` definitions** — joins are performed manually in route handlers.

### 4.2 Registered models (30 tables)

| Domain | Models / Tables |
|---|---|
| Auth | `User` → `users` |
| Clinical | `Patient`, `Laboratory`, `TestCatalog`, `Order`, `OrderItem`, `SampleCollection`, `TestResult`, `ClinicalSummary` |
| B2B / Finance | `Company`, `Contract`, `ContractPrice`, `Invoice`, `Payment` |
| Field ops | `HomeCollection`, `SampleTracking`, `SampleEvent`, `Driver` |
| Dispatch | `DispatchJob`, `DispatchItem` |
| Logistics | `Shipment`, `ShipmentItem`, `ShipmentTimeline`, `TransportBox`, `EventLog` |
| Documents | `ResultFile` |
| Compliance | `AuditLog`, `Alert`, `Incident` |
| CRM | `CrmLead` |

### 4.3 Orphan model

| Model | Table | Status |
|---|---|---|
| `HomeSampling` | `home_sampling_requests` | Not imported in `models/__init__.py`; no API |

### 4.4 Logical relationship map

```
Patient ──< Order ──< OrderItem ──< TestResult
   │                    │
   │                    └──> ClinicalSummary
   │
   └──< HomeCollection ──< SampleTracking ──< SampleEvent
              │                  │
              │                  └──> TransportBox (by ID)
              └──> Driver (collector_id)

Shipment ──< ShipmentItem
    │
    ├──> ShipmentTimeline (1:N events)
    ├──> TransportBox (transport_box_id)
    └──> Driver (collector_id)

User (auth) ──?──> Patient (linked by phone/email at login, not FK)

Company ──< Contract ──< ContractPrice
Order ──> Company, Contract, Laboratory (by ID)
```

### 4.5 Schema management

| Mechanism | Status |
|---|---|
| Alembic | In `requirements.txt`, **not configured** |
| Flask-Migrate | In `requirements.txt`, **not wired** |
| Runtime | `db.create_all()` in `run.py` |
| Install scripts | 6+ scripts embed duplicate schema definitions |

**Risk:** Production schema changes are not versioned or reversible.

---

## 5. API Inventory

**Total API routes:** 124

### 5.1 By domain

| Domain | Endpoints | Key prefixes |
|---|---|---|
| Auth & security | 13 | `/auth`, `/security`, `/admin*` |
| Clinical & orders | 22 | `/patients`, `/orders`, `/test-*`, `/sample-collections` |
| Finance & B2B | 17 | `/companies`, `/contracts`, `/invoices`, `/payments` |
| Field collection | 23 | `/workflow`, `/collector`, `/home-collections`, `/sample-trackings` |
| Logistics | 18 | `/shipments`, `/logistics-v2`, `/transport-boxes`, `/box-qr` |
| Mobile / patient | 16 | `/mobile`, `/patient` |
| AI | 4 | `/ai`, `/ai-v2`, `/v2/ai` |
| Ops & system | 11 | `/system`, `/ops`, `/incidents`, `/alerts`, `/result-files`, `/seeds` |

### 5.2 FP-003 collector shipment API (on branch)

| Method | Endpoint |
|---|---|
| `GET` | `/api/v1/collector/shipments` |
| `POST` | `/api/v1/collector/shipments/<id>/accept` |
| `POST` | `/api/v1/collector/shipments/<id>/start-trip` |

### 5.3 Authentication coverage on APIs

| Protected (JWT) | Unprotected |
|---|---|
| `/api/v1/mobile/me`, `/secure/*` | Most logistics, collector, shipment, workflow endpoints |
| Some routes check roles via session (web only) | `/api/v1/auth/register` accepts any role |

---

## 6. Web Modules

**Total web routes:** 93

### 6.1 Module categories

| Category | Routes | Examples |
|---|---|---|
| Auth | 2 | `/login`, `/logout` |
| Dashboards | 8 | `/dashboard`, `/monitor`, `/executive-v9`, `/finance` |
| Clinical CRUD | 15 | `/patients`, `/orders`, `/results`, `/result-files` |
| Portals | 6 | `/portal/<id>`, `/doctor`, `/my-portal` |
| Field ops | 12 | `/home-collections`, `/collector-mobile`, `/samples` |
| Logistics | 14 | `/shipments`, `/transport-boxes`, `/logistics-v2`, `/iot-box` |
| Dispatch | 7 | `/dispatch*`, `/drivers` |
| Ops | 8 | `/audit`, `/security`, `/alerts`, `/incidents`, `/operations` |
| CRM / B2B | 6 | `/companies`, `/contracts`, `/crm-pipeline` |
| KPI | 4 | `/analytics`, `/tat-kpi`, `/collector-kpi`, `/doctor/kpi` |

### 6.2 Web auth pattern

- Session-based via `app/utils/auth.py` (`login_required`, `role_required`)
- Applied selectively (e.g., collector portal); many admin pages lack consistent guards
- Inline HTML error pages for access denied

### 6.3 FP-003 web additions (on branch)

- `/shipments/<id>/accept`, `/shipments/<id>/start-trip`
- Shipment detail timeline table
- Collector mobile shipments section

---

## 7. Flutter Modules

### 7.1 Staff app — `mobile/dxcon_mobile` (untracked)

| Type | File | Status |
|---|---|---|
| Entry | `lib/main.dart` | Active |
| Config | `lib/core/config/api_config.dart` | Points to Render production URL |
| Theme | `lib/core/theme/app_theme.dart` | Basic Material theme |
| Login | `lib/screens/login_screen.dart` | Wired to auth API |
| Shell | `lib/screens/main_shell.dart` | Role-aware bottom nav |
| Home | `lib/screens/home_screen.dart` | Collector shortcut |
| Shipments | `lib/screens/collector_shipments_screen.dart` | FP-003 accept/start-trip |
| Orders | `lib/screens/orders_screen.dart` | Placeholder |
| Files | `lib/screens/files_screen.dart` | Placeholder |
| Profile | `lib/screens/profile_screen.dart` | Basic |
| Auth service | `lib/services/auth_service.dart` | Login client |
| Collector service | `lib/services/collector_service.dart` | FP-003 API client |

### 7.2 Patient app — `dxcon_patient_app`

| File | Notes |
|---|---|
| `lib/main.dart` | Full web app using `dart:html`; inline HTTP |
| `lib/home_collection_page.dart` | Home collection booking |

Hardcoded `127.0.0.1:8000` — not production-ready.

### 7.3 Flutter gaps

- No shared service layer in patient app
- No environment configuration (dev/staging/prod)
- No Flutter CI
- Staff app not committed to git
- No integration/widget tests beyond boilerplate

---

## 8. Authentication Flow

### 8.1 API authentication (JWT)

```
Client POST /api/v1/auth/login { email, password }
    → User.query.filter_by(email)
    → verify_password (bcrypt via app/core/passwords.py)
    → create_access_token(identity=user.id, claims={role, email})
    → Returns { token, access_token, email, role, user }

Protected mobile routes:
    @jwt_required() on /api/v1/mobile/me, /secure/*
    Identity = user.id; patient resolved by phone match
```

**Issues:**
- `/api/v1/auth/register` allows self-assignment of any `role` (including `SUPER_ADMIN`)
- JWT not enforced on collector, shipment, or logistics APIs
- Mobile login in `mobile/routes.py` is a **separate** patient-only login path

### 8.2 Web authentication (session)

```
Browser POST /login (form)
    → auth_web.login_page verifies password
    → Supports plaintext OR bcrypt (legacy compat in web/auth.py)
    → session["user_id"], session["role"], session["email"]
    → attach_patient_to_session() for PATIENT role

Protected web routes:
    @role_required("SUPER_ADMIN", "COLLECTOR") etc.
```

**Issues:**
- Web auth accepts plaintext password match (backward compat) — security risk
- Inconsistent guard coverage across 93 web routes
- Session secret hardcoded in `__init__.py`

### 8.3 Role model

Roles stored as free-form strings on `User.role` (e.g., `PATIENT`, `COLLECTOR`, `SUPER_ADMIN`, `DOCTOR`). No enum constraint at DB level. Role checks are string comparisons in decorators.

---

## 9. Logistics Workflow

### 9.1 Documented chain of custody

```
Booking → Collector → Sample → Transport Box → Shipment → Lab Receive → Testing → AI → Doctor → Patient
```

(Source: `docs/architecture/LOGISTICS_CHAIN_OF_CUSTODY.md`)

### 9.2 Shipment status machine

**Documented:** `CREATED → IN_TRANSIT → ARRIVED → RECEIVED → TESTING → COMPLETED`

**Implemented (FP-003 on branch):** adds `ACCEPTED` between `CREATED` and `IN_TRANSIT`

| Transition | Trigger | Side effects (FP-003 service) |
|---|---|---|
| `CREATED → ACCEPTED` | Collector accept | Audit + timeline + event; box `ONLINE → IN_USE` |
| `ACCEPTED → IN_TRANSIT` | Start trip | Audit + timeline + event; box → `IN_TRANSIT`; `departed_at` set |
| `IN_TRANSIT → ARRIVED` | `/shipments/<id>/arrived` | Audit only (no timeline/event in service) |
| `* → RECEIVED` | Lab receive (API/web/box QR) | Audit only |

### 9.3 Parallel workflow paths (duplication risk)

| Path | Module | Scope |
|---|---|---|
| Home collection | `/api/v1/workflow/*` | Booking → checkin → collected → sample status |
| Collector jobs | `/api/v1/collector/*` | Same operations, different handlers |
| Sample tracking | `/api/v1/sample-trackings/*` | Standalone sample CRUD |
| Shipments | `/api/v1/shipments/*` + FP-003 collector | Box-level chain of custody |

### 9.4 Transport box lifecycle

| Status | Meaning |
|---|---|
| `ONLINE` | Available |
| `IN_USE` | Assigned / accepted (FP-003) |
| `IN_TRANSIT` | Active trip (FP-003) |
| `RETURNING` | Post lab-receive |

IoT simulation available via `/iot-box/simulate-*` web routes.

---

## 10. QR Workflow

### 10.1 Payload format

```
DXCON:SHIPMENT:<shipment_code>
DXCON:SAMPLE:<sample_code>
DXCON:BOX:<box_code>
```

Parser: `app/core/qr_service.py` → `parse_qr_payload()`

### 10.2 Scan/resolution paths

| Entry point | Behavior |
|---|---|
| `POST /api/v1/logistics-v2/scan` | Parses QR; returns shipment or sample object |
| `GET /api/v1/shipments/scan/<qr_payload>` | Shipment lookup by code |
| `GET /api/v1/box-qr/<box_id>` | Returns box QR payload string |
| `GET /boxes/<box_id>/qr` | Web QR display page |
| `GET /shipments/<id>/qr` | Web shipment QR display |
| `POST /api/v1/shipments/receive-by-box/<box_id>` | Lab receive via box QR |

### 10.3 Gaps

- No unified QR scan service — logic split across logistics_v2 and shipments
- QR scan endpoints are unauthenticated
- No scan event logging standard (some paths write events, others do not)

---

## 11. AI Modules

### 11.1 API surfaces (3 version paths)

| Version | Prefix | Endpoint | Logic location |
|---|---|---|---|
| v1 | `/api/v1/ai` | `POST /interpret` | `services/ai_interpretation.py` |
| v2 | `/api/v2/ai` | `GET /order/<order_id>` | `api/ai/routes_v2.py` |
| v2-alt | `/api/v1/ai-v2` | `GET /order/<order_id>`, `GET /generate-all` | Inline in `ai_v2/routes.py` + `ai_v2/batch.py` |

### 11.2 Services

| Service | Purpose |
|---|---|
| `ai_interpretation.py` | Rule-based result interpretation (v1 API) |
| `ai_summary.py` | Summary generation |
| `ai_risk_engine.py` | Risk scoring |
| `medical_summary.py` | Medical summary assembly |

### 11.3 AI behavior

Current AI modules use **rule-based heuristics** (keyword matching on test names and flags like `HIGH`), not external LLM calls. Results stored in `ClinicalSummary` model.

### 11.4 Gaps

- Three overlapping AI API versions with duplicated interpret logic
- No AI audit trail for clinical decisions
- No doctor-approval gate enforced at API level before patient visibility
- AI endpoints unauthenticated

---

## 12. Test Coverage

| Suite | Location | Cases | CI executed |
|---|---|---|---|
| Collector workflow v1 | `backend/tests/test_collector_workflow_v1.py` | 5 | **No** |
| Flutter widget (staff) | `mobile/dxcon_mobile/test/widget_test.dart` | 1 boilerplate | No |
| Flutter widget (patient) | `dxcon_patient_app/test/widget_test.dart` | 1 boilerplate | No |

### 12.1 What is tested (FP-003)

- Accept shipment → status, box, audit, timeline, event
- Start trip validation and full flow
- Legacy `/shipments/<id>/start` backward compat
- List collector shipments

### 12.2 Coverage estimate

| Area | Estimated coverage |
|---|---|
| API endpoints (124) | ~4% (5 tests on 3 endpoints) |
| Web routes (93) | 0% |
| Services (11) | ~9% (1 of 11 partially) |
| Flutter | 0% meaningful |
| AI modules | 0% |
| Auth / security | 0% |

---

## 13. CI/CD Pipeline

### 13.1 GitHub Actions (`.github/workflows/backend-ci.yml`)

| Trigger | Push/PR to `main` |
|---|---|
| Python | 3.9 |
| Steps | Checkout → pip install → py_compile (2 files) → health_check → check_routes |

### 13.2 Not in CI

- Unit tests (`unittest`)
- Linting (ruff/flake8/mypy)
- Security scanning
- Flutter analyze/build
- Deploy automation
- Database migration validation
- Integration tests against PostgreSQL

### 13.3 Manual verification scripts

| Script | Purpose |
|---|---|
| `health_check.py` | Compile + required route smoke |
| `check_routes.py` | Duplicate route detection |
| `verify_logistics_v2.py` | Logistics v2 route check |
| `go_live_check.py` | Pre-production checklist |
| `check_production.py` | Production validation |

**Missing:** `verify_collector_workflow_v1.py` (planned FP-003 Commit 4)

---

## 14. Technical Debt

| Category | Severity | Description |
|---|---|---|
| Business logic in routes | **Critical** | 86 route modules vs 11 services |
| No DB migrations | **Critical** | `db.create_all()` + install scripts |
| Minimal tests | **Critical** | 5 tests for 217 routes |
| Security gaps | **Critical** | Open APIs, role self-registration, hardcoded secrets |
| Duplicate workflows | **High** | workflow vs collector vs sample_trackings |
| Duplicate AI paths | **High** | 3 AI API versions |
| Inline HTML web UI | **High** | Untestable, no i18n, mixed languages |
| Orphan code | **Medium** | `app.py`, `users_bp`, `HomeSampling`, `.save` files |
| Duplicate blueprint registration | **Medium** | alerts registered twice |
| Install script duplication | **Medium** | 6 scripts re-embed models |
| FP-003 incomplete | **Medium** | Flutter uncommitted; docs/verify missing |
| Non-idempotent service | **Medium** | Repeat accept/start creates duplicate logs |
| Doc drift | **Low** | Architecture doc missing `ACCEPTED` status |

---

## 15. Duplicate Modules

| # | Duplication | Locations |
|---|---|---|
| 1 | Shipment code generation | `api/shipments`, `web/shipments`, install scripts |
| 2 | Shipment lookup | `api/shipments`, `services/collector_workflow` |
| 3 | Sample code generation | `collector/routes`, `workflow/routes`, `sample_trackings/routes`, `web/sample_tracking` |
| 4 | Home collection workflow | `/api/v1/workflow/*` vs `/api/v1/collector/*` |
| 5 | Patient mobile APIs | `/api/v1/mobile/*` vs `/api/v1/patient/*` |
| 6 | Executive dashboards | `executive.py`, `executive_v8.py`, `executive_v9.py` |
| 7 | Dispatch UI | `web/dispatch.py`, `web/logistics.py` on `/dispatch` |
| 8 | Collector portals | `collector_portal`, `collector_console`, `collector_mobile` |
| 9 | AI interpretation | `ai/routes`, `ai/routes_v2`, `ai_v2/routes`, services |
| 10 | Event logging | `core/events`, `services/event_logger`, inline `SampleEvent` |
| 11 | Password verification | `core/passwords.py` vs `web/auth.py` (plaintext fallback) |
| 12 | Lab receive | API receive, web receive, receive-by-box — no shared service |
| 13 | Install scripts | 6 scripts duplicate model/route definitions |
| 14 | Flutter apps | `dxcon_mobile` vs `dxcon_patient_app` |

---

## 16. Missing Features

| Feature | Priority | Notes |
|---|---|---|
| Alembic migrations | Critical | Required for production schema control |
| API authentication on logistics/collector | Critical | Medical chain-of-custody APIs are open |
| Role registration guard | Critical | Anyone can register as SUPER_ADMIN |
| FP-003 Commit 3 (Flutter git) | High | On disk, untracked |
| FP-003 Commit 4 (docs + verify) | High | Not started |
| Idempotent workflow services | High | Retry-safe state transitions |
| Lab receive service | High | Unified receive with full compliance logging |
| Shipment `ARRIVED` compliance logging | High | Currently audit-only |
| Flutter orders/results/files integration | Medium | Placeholder screens |
| Unified patient mobile API | Medium | Two overlapping API surfaces |
| `users_bp` registration or removal | Medium | Dead code |
| `HomeSampling` integration or deprecation | Low | Orphan model |
| Root README | Medium | No project onboarding doc |
| `.env.example` | Medium | Dev setup undocumented |
| Staging environment | Medium | Single production target in config |
| Flutter CI | Medium | No mobile pipeline |
| Rate limiting / API throttling | Medium | Not implemented |
| Photo evidence on lab receive | Low | Documented but not enforced in API |

---

## 17. Security Concerns

| # | Concern | Severity | Location |
|---|---|---|---|
| 1 | Hardcoded Flask secret key | **Critical** | `app/__init__.py` line 106 |
| 2 | Default dev JWT/secret fallbacks | **High** | `core/config.py` |
| 3 | Open registration with arbitrary role | **Critical** | `api/auth/routes.py` register |
| 4 | Logistics/collector APIs unauthenticated | **Critical** | Multiple blueprints |
| 5 | Plaintext password fallback (web) | **High** | `web/auth.py` verify_password |
| 6 | Global CORS without origin filter | **High** | `create_app()` CORS(app) |
| 7 | Admin curl recipe with default password | **Medium** | `backend/super_admin` |
| 8 | No rate limiting on auth endpoints | **Medium** | Auth routes |
| 9 | Session fixation not addressed | **Medium** | Web session auth |
| 10 | No input validation layer (marshmallow unused) | **Medium** | Routes accept raw JSON |
| 11 | SQL injection low risk (SQLAlchemy ORM) | **Low** | Parameterized queries used |
| 12 | No HTTPS enforcement in app layer | **Medium** | Relies on Render TLS |
| 13 | JWT expiry/refresh not documented | **Medium** | JWT config defaults |
| 14 | Seeds endpoint in production | **High** | `/api/v1/seeds/demo-operations` |

---

## 18. Performance Concerns

| # | Concern | Impact | Evidence |
|---|---|---|---|
| 1 | N+1 queries in web dashboards | High | Dashboards loop models with per-row lookups |
| 2 | No pagination on list endpoints | High | `/api/v1/collector/shipments`, `/patients`, etc. return all rows |
| 3 | `db.create_all()` on every startup | Medium | `run.py` runs at boot |
| 4 | No connection pooling config | Medium | Default SQLAlchemy pool |
| 5 | No caching layer | Medium | Dashboard stats computed per request |
| 6 | Inline HTML generation | Low | CPU per request for large tables |
| 7 | Event log queries unbounded | Medium | `/logistics-v2/events` limits 200; others unbounded |
| 8 | 87 blueprints loaded at startup | Low | Memory footprint; acceptable for monolith |
| 9 | No async/background jobs | Medium | AI batch, seed ops run synchronously |
| 10 | SQLite fallback in dev | Low | Not production issue |

---

## 19. Production Readiness Score

### 19.1 Scoring rubric

| Dimension | Weight | Score | Weighted |
|---|---|---|---|
| Architecture & layering | 15% | 35 | 5.3 |
| Security | 20% | 25 | 5.0 |
| Testing & CI | 15% | 20 | 3.0 |
| Schema & data integrity | 15% | 30 | 4.5 |
| Compliance & audit | 10% | 60 | 6.0 |
| Documentation | 5% | 25 | 1.3 |
| Deployment & ops | 10% | 55 | 5.5 |
| Mobile readiness | 5% | 30 | 1.5 |
| Code hygiene | 5% | 40 | 2.0 |
| **Total** | **100%** | | **34.1 → 44** |

*Score adjusted +10 for existing compliance infrastructure (audit/timeline/event tables, chain-of-custody docs, Render deployment, bcrypt, JWT foundation, FP-003 service pattern).*

### 19.2 Verdict

| Rating | Score range |
|---|---|
| **Not production-ready (medical)** | 0–49 |
| Staging-ready with hardening | 50–69 |
| Production-ready | 70–84 |
| Enterprise-grade | 85–100 |

**Score: 44 / 100 — Not production-ready for a regulated medical logistics platform.**

The platform is suitable for **controlled staging/demo** with seeded data. Production deployment requires security hardening, migration pipeline, test coverage, and API auth before handling real patient specimens.

---

## 20. Top 20 Recommendations (Ordered by Impact)

| Rank | Recommendation | Impact | Effort |
|---|---|---|---|
| 1 | **Authenticate all logistics/collector/shipment APIs** (JWT + role guards) | Prevents unauthorized chain-of-custody changes | Medium |
| 2 | **Block self-registration of privileged roles** (SUPER_ADMIN, DOCTOR, COLLECTOR) | Closes critical auth bypass | Low |
| 3 | **Introduce Alembic migrations; remove `db.create_all()` from production boot** | Safe schema evolution | Medium |
| 4 | **Extract business logic into service classes** (shipment, sample, booking, lab-receive) | Testable, auditable, idempotent | High |
| 5 | **Run unit tests in CI; require tests for every API change** | Prevents regressions | Low |
| 6 | **Remove hardcoded secrets; enforce env-only configuration** | Production security baseline | Low |
| 7 | **Unified compliance logger** (audit + timeline + event in one transactional call) | Chain-of-custody integrity | Medium |
| 8 | **Consolidate workflow/collector APIs** behind single service facade | Eliminates drift | High |
| 9 | **Complete FP-003** (commit Flutter, docs, verify script, idempotent service) | Finishes in-flight critical path | Medium |
| 10 | **Add pagination and query limits to all list endpoints** | Performance + DoS mitigation | Medium |
| 11 | **Disable or protect `/api/v1/seeds/*` in production** | Prevents data corruption | Low |
| 12 | **Remove plaintext password fallback in web auth** | Credential security | Low |
| 13 | **Consolidate AI APIs to single versioned surface** | Reduces maintenance | Medium |
| 14 | **Register or delete orphan modules** (`users_bp`, `HomeSampling`, `app.py`) | Reduces confusion | Low |
| 15 | **Resolve duplicate URL registrations** (/collector, /dispatch, /executive) | Predictable routing | Low |
| 16 | **Add Flutter CI** (analyze + widget tests) and commit staff app | Mobile quality gate | Medium |
| 17 | **Replace install scripts with migrations + feature flags** | Eliminates code duplication | Medium |
| 18 | **Add `.env.example` and root README** | Developer onboarding | Low |
| 19 | **Implement lab-receive service with full evidence capture** (GPS, photo, temp) | Regulatory compliance | High |
| 20 | **Merge Flutter apps or establish shared API client package** | Consistent mobile strategy | High |

---

## Appendix A — Route Counts

| Type | Count |
|---|---|
| API routes | 124 |
| Web routes | 93 |
| Static | 1 |
| **Total** | **218** |

## Appendix B — Dependency Highlights

| Package | Version | Used for |
|---|---|---|
| Flask | 3.1.3 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-JWT-Extended | 4.7.1 | Mobile JWT |
| psycopg2-binary | 2.9.12 | PostgreSQL |
| gunicorn | 23.0.0 | Production WSGI |
| bcrypt | 5.0.0 | Password hashing |
| Alembic / Flask-Migrate | Present | **Not configured** |
| reportlab / qrcode / pillow | Present | PDF + QR generation |

## Appendix C — Deployment Summary

| Component | Platform | Config |
|---|---|---|
| API | Render (`dxcon-api`) | `backend/render.yaml` |
| Database | Render PostgreSQL (`dxcon-postgres`) | Connection via `DATABASE_URL` |
| Mobile API target | `https://dxcon-ap.onrender.com` | `mobile/dxcon_mobile/lib/core/config/api_config.dart` |
| CI | GitHub Actions | Backend compile + health + routes only |

---

*Report generated by static repository analysis. No application code was modified during this assessment.*
