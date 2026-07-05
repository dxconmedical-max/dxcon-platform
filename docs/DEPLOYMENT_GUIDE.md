# DxCon Deployment Guide — Enterprise v1.0

## Prerequisites

- PostgreSQL 14+
- Redis (recommended for production queues)
- Docker and Docker Compose (or Kubernetes)
- TLS certificate for public endpoints

See [REQUIRED_ENVIRONMENT_VARIABLES.md](REQUIRED_ENVIRONMENT_VARIABLES.md).

## Deployment Profiles

| Profile | Use case |
|---------|----------|
| Docker Compose | Staging / single-node production |
| Kubernetes | Multi-node production |
| Render | Managed cloud deployment |
| On-premise | Hospital data center |

## Quick Start (Docker Compose)

```bash
cp backend/.env.production.example backend/.env
docker compose -f docker-compose.production.yml up -d
```

## Production Checklist

1. Set strong `SECRET_KEY` and database credentials.
2. Configure `DATABASE_URL` for PostgreSQL.
3. Enable Redis (`REDIS_URL`) for background jobs.
4. Configure SMTP for notifications.
5. Run migrations and verify startup checks.
6. Execute `python scripts/verify_healthcare_ecosystem.py`.

## Health Verification

After deploy, confirm:

- `/ready` returns 200
- `/api/v1/system/health` reports OK
- `/healthcare-ecosystem` dashboard accessible (admin login)

## Rollback

Follow [ROLLBACK_RUNBOOK.md](ROLLBACK_RUNBOOK.md) and Release Control hub at `/release-control`.

## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md)
- [DEPLOYMENT_ARCHITECTURE.md](architecture/DEPLOYMENT_ARCHITECTURE.md)
- [Regional Architecture](architecture/REGIONAL_ARCHITECTURE.md)
