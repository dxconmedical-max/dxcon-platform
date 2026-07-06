# DxCon Production Deployment Guide

## Environment Profiles

| Profile | `APP_ENV` | Database | Notes |
|---------|-----------|----------|-------|
| Development | `development` | SQLite/local PG | Hot reload, debug |
| Testing | `testing` | SQLite memory | CI/CD |
| Staging | `staging` | PostgreSQL | Pre-production |
| Production | `production` | PostgreSQL | Live traffic |

## Configuration Validation

Required environment variables:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dxcon
SECRET_KEY=<random-64-char>
APP_ENV=production
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
UPLOAD_FOLDER=/var/lib/dxcon/uploads
STORAGE_PROVIDER=local  # or s3, minio, azure_blob
```

Validate on startup:

```bash
python backend/scripts/health_check.py
python backend/scripts/verify_release_1.py
```

## Docker Production Stack

`docker-compose.production.yml` includes:

- **api** — Gunicorn via `production_start.py`
- **postgres** — PostgreSQL 16
- **redis** — Session/cache ready
- **nginx** — Reverse proxy with SSL termination
- **worker** — Background jobs ready
- **scheduler** — Cron jobs ready

```bash
docker compose -f docker-compose.production.yml up -d --build
```

## Nginx + Gunicorn

- Nginx config: `deployment/nginx/default.conf`
- Health endpoints: `/live`, `/ready`
- Static uploads served via `/files/`

## Migrations

Apply in order (additive only):

```
001_business_engine_sprint1.sql
004_partner_foundation.sql
005_reception_workspace.sql
006_lab_workspace.sql
007_reporting_engine.sql
008_portal.sql
009_executive_platform.sql
```

```bash
python backend/scripts/apply_migrations.py
```

## Deployment Targets

| Platform | Status | Notes |
|----------|--------|-------|
| Render | Ready | Use Dockerfile + managed PostgreSQL |
| Railway | Ready | Set `DATABASE_URL` from plugin |
| AWS | Ready | ECS/EKS + RDS |
| Azure | Ready | Container Apps + Azure Database |
| DigitalOcean | Ready | App Platform + managed DB |

## CI/CD Pipeline

`.github/workflows/backend-ci.yml`:

1. Compile all Python
2. Unit tests (executive, portal, reporting)
3. Health check
4. Route check
5. Release 1 verification
6. Docker build

## Rollback

```bash
# Redeploy previous image tag
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d api

# Database: restore from backup (see backup dashboard)
```

## Monitoring

- `/app/monitoring` — Operational dashboard
- `/api/v1/metrics` — Prometheus metrics
- `/health` — Health endpoint
- Audit: `/app/audit-center`

## Security Hardening

Enabled in Release 1.0:

- Rate limiting foundation
- Session management
- Password policy
- Account lockout
- Security headers
- CSRF protection
- CORS review
- JWT validation
- Permission audit via RBAC

## Backup

- Manual backup via `/app/backup`
- Scheduled backup configuration in admin settings
- Restore: placeholder — use PostgreSQL `pg_dump` / `pg_restore`
