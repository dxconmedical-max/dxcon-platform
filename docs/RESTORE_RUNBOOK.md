# DxCon Restore Runbook

## Prerequisites

- Validated backup artifact ID
- Maintenance window approved
- Rollback plan reviewed (`docs/ROLLBACK_RUNBOOK.md`)

## Step 1 — Dry Run (Required)

Never skip dry run on production.

```bash
POST /api/v1/operations/restores/dry-run
deployment/scripts/restore_postgres_dry_run.sh
```

Hub: `/backup-recovery/restore`

## Step 2 — Enable Maintenance

```bash
POST /api/v1/operations/maintenance/enable
```

## Step 3 — Stop Workers

1. Scale application replicas to zero or stop container entrypoint
2. Confirm no active background jobs: `/monitoring/background-jobs`

## Step 4 — Restore Database

1. Restore PostgreSQL from latest validated backup
2. Restore uploads/object storage if affected
3. Record restore job via operations API

## Step 5 — Validate

```bash
GET  /api/v1/system/readiness
GET  /api/v1/system/health
python backend/scripts/verify_staging_stack.py
python backend/scripts/smoke_test_staging_stack.py
```

Core tables to spot-check: `users`, `patients`, `medical_orders`, `invoices`

## Step 6 — Resume Service

```bash
POST /api/v1/operations/maintenance/disable
```

## Failure Handling

If restore validation fails:

1. Do not disable maintenance mode
2. Execute rollback per `docs/ROLLBACK_RUNBOOK.md`
3. Open incident with severity CRITICAL

## RTO / RPO Targets

| Tier           | RTO    | RPO   |
|----------------|--------|-------|
| Production API | 4 hrs  | 1 hr  |
| File storage   | 8 hrs  | 4 hrs |

## Related Docs

- `docs/RESTORE.md`
- `docs/DISASTER_RECOVERY.md`
