# DxCon System Architecture — Enterprise v1.0

## Overview

DxCon is a multi-tenant healthcare diagnostics platform spanning lab operations, clinic workflows, home collection, AI-assisted interpretation, regional cloud deployment, and partner marketplace integration.

## Release

| Field | Value |
|-------|-------|
| Version | 1.0.0-rc1 |
| Phase | 10 — Healthcare Ecosystem |
| Hub | `/healthcare-ecosystem` |

## Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Ecosystem Hub (Phase 10) · Governance · Commercial Release   │
├──────────────────────────────────────────────────────────────┤
│  Regional Cloud (Phase 9) · Intelligent AI (Phase 8)        │
├──────────────────────────────────────────────────────────────┤
│  Enterprise Platform (Phase 5–7) · Multi-tenant · Marketplace │
├──────────────────────────────────────────────────────────────┤
│  Core Operations: Lab · Clinic · Home · Billing · Results    │
├──────────────────────────────────────────────────────────────┤
│  Flask API · PostgreSQL · Redis · Object Storage             │
└──────────────────────────────────────────────────────────────┘
```

## Product Modules

| Product | Primary route | Status |
|---------|---------------|--------|
| DxCon Lab | `/lab-operations` | READY |
| DxCon Clinic | `/clinic-portal` | READY |
| DxCon Home | `/collector` | READY |
| DxCon AI | `/intelligent-healthcare` | READY |
| DxCon Cloud | `/regional-cloud` | READY |
| DxCon Marketplace | `/marketplace-platform` | READY |
| DxCon Pharmacy | scaffold | v2 |
| DxCon Insurance | scaffold | v2 |

## Governance Boards

- **Architecture Board** — system and domain architecture docs
- **Release Board** — version, migration, rollback control
- **Medical Governance** — advisory-only AI, human review mandatory
- **Security Governance** — RBAC, audit, compliance exports
- **AI Governance** — prompt audit, PHI redaction, safety layer

## Data & Persistence

- **Production:** PostgreSQL only (SQLAlchemy ORM)
- **Tests/verify:** SQLite in-memory permitted
- **Migrations:** Non-destructive additive changes only

## Related Documentation

- [Regional Architecture](architecture/REGIONAL_ARCHITECTURE.md)
- [AI Architecture](architecture/AI_ARCHITECTURE.md)
- [Tenant Architecture](architecture/TENANT_ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Operations Guide](OPERATIONS_GUIDE.md)
