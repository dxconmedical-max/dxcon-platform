# Changelog

All notable changes for DxCon production releases.

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
