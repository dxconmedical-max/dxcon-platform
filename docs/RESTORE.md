# DxCon Restore Guide

## Dry Run (Required First)

```bash
POST /api/v1/operations/restores/dry-run
deployment/scripts/restore_postgres_dry_run.sh
```

## Restore Procedure

1. Enable maintenance mode: `POST /api/v1/operations/maintenance/enable`
2. Stop application workers
3. Restore database from latest validated backup
4. Restore uploads/object storage if needed
5. Run smoke tests: `backend/scripts/smoke_test_staging_stack.py`
6. Disable maintenance: `POST /api/v1/operations/maintenance/disable`

## Validation

- `GET /api/v1/system/readiness`
- `backend/scripts/verify_staging_stack.py`
- `backend/tests/test_backup_restore.py`

## Rollback

If restore fails, revert to previous deployment tag and prior backup set. See `docs/DISASTER_RECOVERY.md`.
