# DxCon Backup Guide

## Scope

- PostgreSQL database
- Uploaded files (`STORAGE_PATH` / object storage)
- Configuration secrets (external secret manager)

## Automated Backups

Operations API:

- `GET /api/v1/operations/backups`
- `POST /api/v1/operations/backups/run`

Deployment scripts:

```bash
deployment/scripts/backup_postgres.sh
deployment/scripts/backup_uploads.sh
```

## Backup Validation

```bash
POST /api/v1/operations/backups/<backup_id>/validate
cd backend && ./venv/bin/python scripts/backup_restore_lib.py
```

## Retention

Configure retention in deployment environment (`deployment/env/`). Production should retain daily backups for at least 30 days.

## Reports

`backend/generated_release/backup_review.json` from Enterprise Pack 5 verification.
