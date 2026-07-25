# Release Notes — DxCon v1.0.0

## Summary

**DxCon Release 1.0.0 is frozen.**  
Branch `feature/reception-m1` is merged into `release/v1.0.0` and tagged `v1.0.0`. Authentication remains **frozen**. Admin module was unchanged by this merge. Release 2 has **not** been started.

| Field | Value |
|-------|--------|
| Version | `1.0.0` |
| Tag | `v1.0.0` |
| Branch | `release/v1.0.0` |
| Freeze merge | `86f3d8516bb6a5315314076b78cc224a737539b8` |
| Auth | Frozen |

## What’s in

- End-to-end clinical path: Reception → Collection → Laboratory → PDF report → role dashboards
- **Reception M1 UI:** patient search/create, test catalog, authoritative pricing, order create/confirmation
- Production API security gate (rc1): JWT/session on high-risk APIs, PATIENT-only register, demo/seed locks, signed downloads
- Health / live / ready probes (including `/ready` migration re-verify)
- Flutter Mobile Phase 1 foundation
- Auth freeze CI guards

## What’s not (Release 2+ / later)

- Reception M2 payment & receipt product track (as a new release)
- Reception barcode / QR / requisition UX completion track
- Alembic-managed migrations
- Flutter Phase 2/3
- Hardened CSP without `unsafe-inline` / `unsafe-eval`

## Upgrade notes

1. Set `BUILD_VERSION=1.0.0`, `API_AUTH_GATE_ENABLED=true`, `DEMO_MODE=false`.
2. Deploy web from `v1.0.0` / `release/v1.0.0`; deploy API matching the same tip when promoting.
3. Apply outstanding SQL migrations per ops runbook.
4. Keep auth freeze paths untouched except via hotfix policy.
5. Staff users must be provisioned by admins — public register is PATIENT-only.

## Verification (Release Freeze)

| Gate | Result |
|------|--------|
| Auth frozen / unchanged | PASS |
| Admin unchanged | PASS |
| Reception M1 production verification | PASS (RM acceptance) |
| Auth-freeze Vitest + verify | PASS |
| Reception M1 Vitest | PASS |
| Backend reception + RC security | PASS |
| Frontend production build | PASS |

## Support

- `docs/RELEASE_1_FINAL_REPORT.md`
- `docs/RELEASE_FREEZE_REPORT.md`
- `docs/AUTH_FREEZE.md`
- `docs/DEPLOYMENT.md`
