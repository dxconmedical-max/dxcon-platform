# DxCon RC Audit Report — v1.0.0-rc1

**Date:** 2026-07-24  
**Scope:** System audit, security, hardening, DB, observability, testing posture  
**Auth:** FROZEN — web auth runtime not modified

---

## P0

| ID | Title | Status |
|----|-------|--------|
| RC-P0-001 | Unauthenticated high-risk APIs (patients/orders/billing/collector/…) | **Mitigated** — `API_AUTH_GATE` requires JWT/session in strict env |
| RC-P0-002 | Public register accepts privileged roles | **Fixed** — PATIENT-only |
| RC-P0-003 | Unauthenticated demo seed / credential dump | **Fixed** — blocked when `APP_ENV=production` and `DEMO_MODE=false` |
| RC-P0-004 | Files download without signed URL; list/upload open | **Fixed** — JWT + mandatory signed download |
| RC-P0-005 | Unauthenticated security admin user/role APIs | **Fixed** — `roles_required(ADMIN+)` + gate |
| RC-P0-006 | No Alembic / incomplete migration runner | **Open** — manual SQL; duplicate `007` renumbered to `016` |
| RC-P0-007 | Worker/scheduler placeholders in production compose | **Open** |
| RC-P0-008 | Render Redis/SMTP not auto-provisioned | **Open** — `sync: false` keys added; ops must set |

---

## P1

| ID | Title | Status |
|----|-------|--------|
| RC-P1-001 | In-memory rate limiter (multi-instance weak) | Open |
| RC-P1-002 | Backend CI historically narrow | **Improved** — workflow expanded for RC suites |
| RC-P1-003 | Web CI beyond auth-freeze | Open |
| RC-P1-004 | CSP `unsafe-inline` / `unsafe-eval` | Open (auth freeze / XSS residual) |
| RC-P1-005 | Refresh unknown jti treated as valid | **Fixed** — missing jti ⇒ revoked |
| RC-P1-006 | HSTS missing | **Fixed** — set in strict env |
| RC-P1-007 | `.env.local` / zip / `.vercel` not ignored | **Fixed** — `.gitignore` |
| RC-P1-008 | QUEUE_PROVIDER=memory default | Open |
| RC-P1-009 | Tenant middleware non-enforcing on legacy | Open |
| RC-P1-010 | Auth freeze: non-HttpOnly soft cookies / token storage | Documented only (freeze) |
| RC-P1-011 | Mobile SENTRY_DSN empty in prod config | Open (approved config required) |
| RC-P1-012 | Prometheus auth default | Open (prefer enable in prod) |

---

## P2

| ID | Title |
|----|-------|
| RC-P2-001 | Virus scan no-op |
| RC-P2-002 | S3 silent `/tmp` fallback if boto missing |
| RC-P2-003 | Flutter local SDK builds incomplete; CI present |
| RC-P2-004 | Doctor/Patient inbox UIs thin shells |
| RC-P2-005 | E2E often SQLite — re-run on Postgres before GA |

---

## Ready summary (what is solid)

- CORS hardening for strict env; security headers baseline
- Health / live / ready probes
- Correlation / request IDs + JSON logging path
- Reception → Sample Collection → Lab → Report PDF → Role dashboards (committed)
- Auth freeze CI (`test:auth-freeze` / `verify:auth-freeze`)
- Flutter Phase 1 foundation (`apps/mobile`)

---

## Release Candidate decision

**v1.0.0-rc1 is prepared for controlled cutover testing.**

**Not GA-ready** until remaining **open P0** items (migration runner discipline, real workers, Redis/SMTP on Render) are closed and production Postgres E2E is signed off.

**Do not start new product features on this RC branch.** Security/docs/tests only.
