# Changelog

All notable changes for DxCon production releases.

## [1.0.0] — 2026-07-25 — RELEASE FREEZE

**Status:** Release 1 **FROZEN** on `release/v1.0.0`.  
**Tag:** `v1.0.0`  
**Merge:** `feature/reception-m1` → `release/v1.0.0` (`86f3d85`)

### Added
- Reception Milestone 1 production workflow UI: patient search/create, catalog selection, authoritative pricing, order create/confirmation (`7729a9c`).
- Go-live verification report (`21b8978`).
- Release freeze package: `docs/RELEASE_1_FINAL_REPORT.md`, `docs/RELEASE_FREEZE_REPORT.md`, project status / system baseline / M1 sign-off artifacts.

### Fixed
- `/ready` re-verifies migrations in request context (`ad0beb1`).

### Security (carried from rc1)
- Production API auth gate, PATIENT-only public register, demo/seed locks, signed file downloads, HSTS in strict envs.

### Verification (freeze gate)
- Auth freeze unchanged — PASS
- Admin module unchanged — PASS
- Reception M1 production verification — PASS (Release Manager acceptance)
- Local CI gates (auth-freeze, M1 Vitest, backend reception+RC security) — PASS
- Frontend production build — PASS

### Known
- Residual: post-create browser order GET `status 0` observed once during automated PV; tracked for hotfix policy (see freeze report).
- Release 2 not started.

## [1.0.0-rc1] — 2026-07-24

### Security
- Production API auth gate for high-risk `/api/v1/*` prefixes (JWT or session).
- Public registration restricted to `PATIENT` role.
- Demo seed and pilot toolkit blocked in production unless `DEMO_MODE`.
- File APIs require JWT; downloads require signed URL.
- Security admin APIs require ADMIN+ roles.
- Refresh tokens: unknown `jti` treated as revoked.
- HSTS enabled in strict environments.
- Ignore local secret artifacts (`.env.local`, `.vercel/`, zip dumps).

### Added (prior commits on branch)
- Reception M1–M4 (order, payment, documents, lab handoff).
- Sample Collection production workflow through lab arrival.
- Laboratory Workflow through medical validation.
- Production Report PDF (`dxcon-clinical-report-v1@1.0.0`).
- Role dashboards + synthetic E2E go-live validation.
- Flutter Mobile Phase 1 foundation.

### Fixed
- Duplicate migration number `007_reporting_engine.sql` → `016_reporting_engine.sql`.
- Render blueprint `BUILD_VERSION` → `1.0.0-rc1`; expanded CORS; Redis/SMTP placeholders.

### Known
- See `docs/RC_AUDIT_REPORT.md` open P0/P1.
