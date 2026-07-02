# DxCon Disaster Recovery

## Objectives

| Tier | RTO | RPO |
|------|-----|-----|
| Production API | 4 hours | 1 hour |
| File storage | 8 hours | 4 hours |

## Failure Scenarios

### Database loss

1. Fail over to standby (if configured) or restore from latest backup
2. Follow `docs/RESTORE.md`
3. Validate core tables: users, patients, orders

### Region / cluster loss

1. Provision standby stack from `deployment/` manifests
2. Restore PostgreSQL + object storage
3. Update DNS/ingress to standby
4. Run Enterprise Pack 10 sign-off verification

### Application regression

1. `GET /api/v1/operations/deployment/rollback-plan`
2. Redeploy prior container tag (`BUILD_VERSION`)
3. Confirm smoke and security preflight pass

## Communication

- Page on-call via Alertmanager (`deployment/monitoring/alertmanager/alertmanager.yml`)
- Record incident in operations audit trail

## Testing

Quarterly DR drill:

```bash
deployment/scripts/restore_postgres_dry_run.sh
backend/scripts/verify_backup_restore.py
```

Decision artifact: `backend/generated_release/go_live_decision.json`
