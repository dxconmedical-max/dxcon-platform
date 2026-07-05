# DxCon Backup Runbook

## Scope

- PostgreSQL database
- Uploaded files (`STORAGE_PATH` / object storage)
- Configuration secrets (external secret manager — not in git)

## Scheduled Backups

Default cron recommendation: `0 2 * * *` (02:00 UTC daily)

Operations API:

```bash
GET  /api/v1/operations/backups
POST /api/v1/operations/backups/run
```

Hub dashboard: `/backup-recovery`

## Manual Backup Procedure

1. Confirm no restore job in progress: `GET /api/v1/operations/restores`
2. Trigger database backup:
   ```bash
   deployment/scripts/backup_postgres.sh
   ```
3. Trigger uploads backup:
   ```bash
   deployment/scripts/backup_uploads.sh
   ```
4. Validate artifact:
   ```bash
   POST /api/v1/operations/backups/<backup_id>/validate
   ```

## Retention Policy

| Environment | Minimum Retention |
|-------------|-------------------|
| Production  | 30 daily backups  |
| Staging     | 7 daily backups   |

Configure retention in `deployment/env/` templates.

## Verification

```bash
cd backend
DATABASE_URL=sqlite:///:memory: python scripts/verify_backup_recovery.py
python scripts/backup_restore_lib.py
```

Report: `backend/generated_release/BACKUP_RECOVERY_REPORT.json`

## Escalation

If backup job fails twice consecutively, open incident per `docs/INCIDENT_RUNBOOK.md` with severity HIGH.

## Related Docs

- `docs/BACKUP.md`
- `docs/DISASTER_RECOVERY.md`
- `/backup-recovery/runbook`
