# DxCon Pilot Deployment Guide

This guide covers deploying DxCon Release 1.0 for a pilot laboratory or clinic network.

## Prerequisites

- PostgreSQL 16+
- Docker and Docker Compose (recommended)
- Domain with SSL certificate
- SMTP credentials for notifications

## Quick Start (Docker)

```bash
# Clone and configure
cp deployment/env/production.env.example deployment/env/production.env
# Edit DATABASE_URL, SECRET_KEY, SMTP settings

# Start production stack
docker compose -f docker-compose.production.yml up -d

# Apply migrations (first run)
docker compose -f docker-compose.production.yml exec api python scripts/apply_migrations.py

# Verify
docker compose -f docker-compose.production.yml exec api python scripts/verify_release_1.py
```

## Pilot Wizard

1. Log in as `SUPER_ADMIN`
2. Navigate to `/app/pilot/wizard`
3. Complete checklist:
   - Organization setup
   - Admin user
   - Laboratory configuration
   - Clinic configuration
   - Master data import
   - Test data
   - Verification

## Seed Master Data

```bash
python backend/scripts/seed_mdm_demo.py   # if available
python backend/scripts/verify_partner_foundation.py
```

## Pilot Users

| Role | Purpose |
|------|---------|
| SUPER_ADMIN | Platform administration |
| RECEPTION | Front desk operations |
| LAB | Laboratory workspace |
| DOCTOR | Report review and approval |
| PATIENT | Patient portal access |

Use `/login/demo?role=DOCTOR` for demo accounts or create via admin.

## Verification

```bash
cd backend
python scripts/verify_release_1.py
python scripts/verify_reporting_engine.py
python scripts/verify_portal.py
python scripts/verify_laboratory_workspace.py
```

All scripts should report PASS before go-live.

## Support

- Executive dashboard: `/app/executive`
- Monitoring: `/app/monitoring`
- Audit center: `/app/audit-center`
- Support: `/app/support`

Contact: support@dxcon.test
