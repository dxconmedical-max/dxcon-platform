# DxCon Production Integration — Current-State Discovery

**Release:** 8.1 · **Sprint:** 9 — Web Application Cutover and Production Validation
**Generated:** 2026-07-13
**Method:** Verified from live code and Git history. Prior agent reports were **not** trusted.

---

## 1. Git topology (verified)

| Item | Value |
| --- | --- |
| Discovery branch | `release/8.0-patient-commerce` (Sprint 7 tip) |
| Integration branch created | `release/8.1-production-integration` |
| Base commit (Sprint 7 tip) | `456fabbea3ced2f91f4cc3bd5b628f42013691b4` |
| `main` / `origin/main` | `b8ae528586a0c20cbd7e72256718a8c2a89ceeb0` (Release 3.0 Epic 10) |
| Commits on tip not on `main` | 9 |

### Critical finding: the release branches are a **single linear stack**

All sprint branches are **direct ancestors** of the Sprint 7 tip. Integration has effectively already happened linearly; there are **no divergent branches to merge**.

```
456fabb  Release 8.0 Sprint 7 - Patient Commerce Platform      (tip / base for 8.1)
b69e655  Release 8.0 Sprint 6 - Clinical Workflow & Governance
b3e1c54  Release 7.0 - Sprint 5 Analyzer Integration
60240f4  Release 7.0 Sprint 4 - IoT Logistics and Cold Chain
52db081  Release 7.0 Sprint 3 - LIMS Core
af69576  Production Sprint 2 - Patient/Reception/Collector/Lab/Doctor Workspaces
d2add80  Production Sprint 1 - Authentication App Shell and Pilot Workspaces
b8ae528  main (Release 3.0 Epic 10)
```

`git merge-base --is-ancestor <branch> HEAD` returns true for **every** branch below:

| Branch | Head | Ancestor of tip? |
| --- | --- | --- |
| `release/6.0-auth-shell` | af69576 | ✅ yes |
| `release/7.0-lims-core` | 52db081 | ✅ yes |
| `release/7.0-iot-logistics` | 60240f4 | ✅ yes |
| `release/7.0-analyzer-integration` | b3e1c54 | ✅ yes |
| `release/8.0-clinical-workflow` | b69e655 | ✅ yes |
| `feature/collector-lab-workflow` | dd38d37 | ✅ yes (0 commits ahead of tip) |

**Consequence:** No blind branch merges are required. The base commit `456fabb` already contains Sprints 1–8.

---

## 2. Deployment commits (requires manual dashboard confirmation)

The Vercel and Render live commit SHAs **cannot be read from the repository** — they live in the hosting dashboards. This must be confirmed by an operator:

- **Vercel (frontend)** production deployment → confirm it is a descendant of `main` and note the deployed SHA. Root Directory is expected to be `apps/web` (monorepo). No `vercel.json` exists, so Root Directory is a dashboard setting.
- **Render (backend)** service `dxcon-api` → deploy source and last-deployed SHA. `backend/render.yaml` pins `APP_ENV=production`, health check `/api/v1/system/health`.

> **Blocker (informational):** Until confirmed, treat production as "landing page only" per the mission statement.

---

## 3. Production environment configuration (verified in code)

### Frontend (`apps/web`)
- Env module: `apps/web/src/lib/env.ts` (+ re-exports in `apps/web/src/lib/constants.ts`).
- Build-time guard: `apps/web/next.config.ts` (lines 3–23) **throws** in production if any of `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_PUBLIC_SITE_URL`, `NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_APP_ENV` is missing, or if `NEXT_PUBLIC_DEMO_MODE=true`.
- Runtime guard: `collectEnvErrors()` / `assertProductionEnv()` also reject localhost URLs in production.
- Production defaults: `API_BASE_URL=https://api.dxcon.com.vn`, `PUBLIC_SITE_URL=https://dxcon.com.vn`, `APP_URL=https://app.dxcon.com.vn`.
- **Vercel Root Directory:** `apps/web` (dashboard setting; no `vercel.json`). Package manager: **npm** (`apps/web/package-lock.json` present).

### Backend (`backend`)
- Config: `backend/app/core/config.py`. Domains (lines 140–142): `PUBLIC_SITE_URL`, `WEB_APP_URL`, `API_BASE_URL` default to the three production hosts.
- `CORS_ORIGINS` default `*` (line 62), overridden by env. `DEMO_MODE` default `false` (line 143).
- Production readiness guardrails: `backend/app/infrastructure/production_readiness.py` blocks wildcard CORS, SQLite, missing Redis, and missing SMTP in strict envs (`production/prod/live/staging/stage/uat`).

---

## 4. Backend CORS (verified)

- Init: `backend/app/core/security.py` `init_security()` (lines 20–47).
  - Wildcard `*` in a strict env is forced to empty (blocks wildcard-with-credentials).
  - Explicit list → `supports_credentials=True`, scoped to `/api/*`.
- Intended production allowlist (from `backend/.env.production.example`): `https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn`.
- **Gap:** `backend/render.yaml` does **not** set `CORS_ORIGINS`, `REDIS_URL`, or SMTP vars — these must be added in the Render dashboard or the service will fail production readiness. See `docs/PRODUCTION_CORS_VERIFICATION.md`.

---

## 5. Login implementation (verified)

- Page: `apps/web/src/app/login/page.tsx` — client component, calls `useAuth().login()`. **No mock/hardcoded credentials.** Demo banner only shown when `DEMO_MODE=true` (off in prod).
- Auth service: `apps/web/src/lib/api/auth.ts` (re-exported by `apps/web/src/services/auth.ts`). Real endpoints only (see §9).

---

## 6. AppShell implementation (verified)

- `apps/web/src/components/layout/AppShell.tsx` guards each workspace via `useRequireAuth(workspacePath)`; renders spinner while hydrating, `null` when unauthenticated (no clinical-data flash).
- Server edge gate: `apps/web/src/middleware.ts` cookie check (`dxcon_authenticated=1`).
- Permission-filtered menu: `apps/web/src/lib/workspace-nav.ts` `buildWorkspaceNavItems(capabilities)`.
- Shell parts live in `apps/web/src/components/layout/`: `AppShell`, `Header` (+ `MobileNav`, user menu, org switcher), `Sidebar`, `WorkspaceScreen`, `WorkspaceHome`, `RoleWorkspace*`, `Breadcrumb`, `AppWorkspaceRedirect`.

---

## 7. Domain-aware routing (verified — already implemented)

- `apps/web/src/middleware.ts`:
  - `www.dxcon.com.vn` → 308 redirect to apex.
  - Public host + application path → redirect to `APP_URL` (`app.dxcon.com.vn`).
  - Legacy `/admin,/doctor,/patient,/lab,/collector,/clinic` → `/app/*`.
  - Protected `WORKSPACE_ROUTES` without auth cookie → `loginUrl(host)` with `?next=`.
  - Unknown `/app/*` (authed) → rewrite `/app/not-found`.
- Host helpers: `apps/web/src/lib/domains.ts` (`PUBLIC_SITE_HOSTS`, `APP_HOSTS`, `isPreviewHost`). No hardcoded Vercel preview hostname; unknown hosts are treated as `preview` (previews stay usable).
- Cross-domain sign-in: `apps/web/src/lib/urls.ts` `loginUrl(host)` → `https://app.dxcon.com.vn/login` from public host in production.

---

## 8. Frontend routes (verified — no duplicates/conflicts)

**Public** (served on `dxcon.com.vn`): `/`, `/services`, `/partners`, `/pricing`, `/contact`, `/book-demo`, `/privacy`, `/terms` — all present.
**App/auth** (served on `app.dxcon.com.vn`): `/login`, `/register`, `/forgot-password`, `/reset-password`, `/select-organization`, `/session-expired`, `/forbidden`, `/service-unavailable` — all present.
**Workspaces:** `/app`, `/app/admin`, `/app/executive`, `/app/reception`, `/app/doctor`, `/app/clinic`, `/app/lab`, `/app/collector`, `/app/patient` (+ `/app/operations`, `/app/support`, `/app/not-found`). 61 `page.tsx` files total. No duplicated route trees detected.

---

## 9. Backend API (verified — no invented endpoints)

- Health: `GET /api/v1/system/health` (`backend/app/api/system/routes.py`). Also `/live`, `/ready`, `/version`, `/metrics`.
- Auth (`backend/app/api/auth/routes.py`, prefix `/api/v1/auth`):
  `POST /login`, `POST /refresh`, `POST /logout`, `GET /me`, `GET /memberships`, `POST /switch-organization`, `GET /capabilities` (permissions + features), `POST /forgot-password`, `POST /register`, `POST /reset-password`.
- **Frontend↔backend endpoint paths match exactly.** There is **no** separate feature-flags endpoint — features come from `/capabilities`.
- **Known limitation:** `POST /api/v1/auth/reset-password` returns **501 `RESET_NOT_ENABLED`** (not implemented). The reset page exists but the backend flow is disabled.

---

## 10. Unmerged migrations

None divergent. Because the stack is linear, migrations `001`–`020` are all present in the base commit in order (see `docs/PRODUCTION_MIGRATION_RUNBOOK.md`). No migration exists on a branch that is not already an ancestor of the base commit.

---

## 11. Duplicated models or APIs

None found that conflict. The linear history means each sprint added its module (`lims_core`, `iot_logistics`, `analyzer_integration`, `clinical_workflow`, `patient_marketplace`, etc.) on top of the prior state rather than in parallel, so there are no duplicate model definitions to reconcile.

---

## 12. Sprint status classification (verified from code + history)

| Sprint | Scope | Classification | Evidence |
| --- | --- | --- | --- |
| Sprint 1 | Auth + App Shell + pilot workspaces | **VERIFIED_AND_MERGED** (into stack) | `d2add80` ancestor; login/AppShell/middleware present |
| Sprint 2 | Patient/Reception/Collector/Lab/Doctor workspaces | **VERIFIED_AND_MERGED** | `af69576` ancestor; `/app/*` routes present |
| Sprint 3 | LIMS Core | **VERIFIED_AND_MERGED** | `52db081` ancestor; `016_lims_core.sql`, lab routes |
| Sprint 4 | IoT Logistics / Cold Chain | **VERIFIED_AND_MERGED** | `60240f4` ancestor; `017_iot_logistics.sql`, `/app/operations/logistics` |
| Sprint 5 | Analyzer Integration | **VERIFIED_AND_MERGED** | `b3e1c54` ancestor; `018_analyzer_integration.sql`, `/app/lab/analyzers` |
| Sprint 6 | Clinical Workflow & Result Governance | **VERIFIED_AND_MERGED** | `b69e655` ancestor; `019_clinical_workflow.sql`, `/app/lab/result-review`, `/app/doctor/review` |
| Sprint 7 | Patient Commerce | **VERIFIED_AND_MERGED** | `456fabb` tip; `020_patient_commerce.sql`, `/app/patient/book`, marketplace |
| Sprint 8 | Collector/Lab workflow additions | **VERIFIED_AND_MERGED** | `feature/collector-lab-workflow` (dd38d37) is an ancestor with 0 commits ahead |

> "MERGED" here means **merged into the linear release stack** (the base commit), **not** merged into `main` and **not** deployed to production. `main` remains at Release 3.0. Nothing below is LIVE until deployed and smoke/UAT-verified.

---

## 13. Deliverables produced by Sprint 9

- `docs/PRODUCTION_INTEGRATION_CURRENT_STATE.md` (this file)
- `generated-release/PRODUCTION_INTEGRATION_DISCOVERY.json`
- `docs/PRODUCTION_BRANCH_INTEGRATION_ORDER.md`
- `docs/VERCEL_PRODUCTION_ENVIRONMENT.md`
- `docs/PRODUCTION_AUTH_CONTRACT.md`, `docs/WEB_SESSION_SECURITY.md`
- `docs/PRODUCTION_CORS_VERIFICATION.md`
- `docs/APP_SUBDOMAIN_DNS.md`
- `docs/PRODUCTION_MIGRATION_RUNBOOK.md`, `generated-release/PRODUCTION_MIGRATION_REPORT.json`
- `docs/STAGING_DEPLOYMENT_RUNBOOK.md`
- `apps/web/scripts/production-smoke-test.mjs`, `backend/scripts/production_api_smoke_test.py`
- `docs/PRODUCTION_UAT_SPRINT_6_7.md`
- `generated-release/PRODUCTION_INTEGRATION_SECURITY_REPORT.json`
