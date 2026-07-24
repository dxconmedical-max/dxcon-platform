# Release Notes — DxCon v1.0.0-rc1

## Summary

First Production Release Candidate for the DxCon clinical operations platform (web + API + Flutter Phase 1). Authentication is production-verified and **frozen**.

## What’s in

- End-to-end clinical path: Reception → Collection → Laboratory → PDF report → role dashboards
- Hardened production API gate for previously open high-risk endpoints
- Health / live / ready probes, structured logging with correlation IDs
- Mobile Phase 1: secure session storage, login/logout, role routing, API client, offline-safe reads

## What’s not (yet)

- Alembic-managed migrations (manual SQL still required)
- Fully wired production workers/schedulers in Docker Compose
- Flutter Phase 2/3 (patient portal / collector field workflows)
- Hardened CSP without `unsafe-inline` / `unsafe-eval` (requires auth freeze exception for token storage redesign)

## Upgrade notes

1. Set `API_AUTH_GATE_ENABLED=true`, `DEMO_MODE=false`.
2. Apply migrations including renamed `016_reporting_engine.sql`.
3. Expect **401** on anonymous calls to legacy patients/orders/billing/files/security APIs.
4. Staff users must be provisioned by admins — public register is PATIENT-only.

## Verification

- Backend: `python -m unittest tests.test_rc_security_gate -v`
- Auth freeze: `npm run test:auth-freeze` / `npm run verify:auth-freeze` (apps/web)
- E2E: `backend/scripts/e2e_dashboard_go_live.py` (prefer Postgres)

## Support

Ops runbooks: `docs/GO_LIVE_CHECKLIST.md`, `docs/DEPLOYMENT.md`, `docs/INCIDENT_RESPONSE.md`.
