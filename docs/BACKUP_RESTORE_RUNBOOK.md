# Backup & Restore Runbook (Pilot)

## Goals

- Verify tooling (`pg_dump`, `pg_restore`) is available
- Verify `DATABASE_URL` is set and points to PostgreSQL
- Provide a **dry-run** rehearsal that does not touch production DB by default

## Dry-run rehearsal

```bash
python backend/scripts/backup_restore_rehearsal.py --dry-run
```

Report:
- `backend/generated_release/BACKUP_RESTORE_REHEARSAL_REPORT.json`

## Real rehearsal (staging only)

1. Export:

```bash
pg_dump "$DATABASE_URL" > backup.sql
```

2. Restore into staging database:

```bash
pg_restore --clean --if-exists --no-owner --no-privileges -d "$STAGING_DATABASE_URL" backup.sql
```

3. Run:

```bash
python backend/scripts/verify_production_readiness.py
```

## Notes

- Do **not** run restore against production unless you are in a controlled incident response.
- Keep backups encrypted at rest and access-controlled.

