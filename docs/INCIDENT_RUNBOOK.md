# DxCon Incident Runbook

## Severity Levels

| Level    | Examples                                      | Response Time |
|----------|-----------------------------------------------|---------------|
| CRITICAL | API down, data loss, security breach           | 15 minutes    |
| HIGH     | Backup failure, queue backlog, payment blocked | 30 minutes    |
| MEDIUM   | Elevated error rate, degraded AI provider      | 2 hours       |
| LOW      | Non-critical feature degradation               | Next business day |

## Triage Steps

1. **Identify** — collect `request_id` / trace ID from logs or `/monitoring`
2. **Classify** — assign severity and incident type
3. **Communicate** — page on-call via Alertmanager
4. **Mitigate** — maintenance mode, scale, rollback, or failover
5. **Resolve** — fix root cause and validate
6. **Review** — post-incident summary within 48 hours

## Quick Diagnostics

```bash
GET /api/v1/system/health
GET /api/v1/system/ready
GET /api/v1/monitoring-center/dashboard
GET /api/v1/operations/backups
```

Hubs:

- `/monitoring` — application, queue, database health
- `/ai-operations/incident-summary` — AI-specific failures
- `/backup-recovery` — backup and restore status
- `/pilot-status/alerts` — pilot environment alerts

## Common Scenarios

### API Unavailable

1. Check container/pod status and recent deploys
2. Review `/monitoring/application-health`
3. Rollback if tied to recent release (`docs/ROLLBACK_RUNBOOK.md`)

### Database Connectivity

1. `/monitoring/database-health`
2. Verify connection pool and migration status
3. Fail over or restore per `docs/RESTORE_RUNBOOK.md`

### Backup Failure

1. `/backup-recovery/scheduler`
2. Re-run backup manually
3. Escalate HIGH if two consecutive failures

### AI Provider Degradation

1. `/ai-operations/model-health`
2. Switch provider or disable AI features temporarily
3. Review `/ai-operations/incident-summary`

## Maintenance Windows

```bash
POST /api/v1/operations/maintenance/schedule
POST /api/v1/operations/maintenance/enable
# perform work
POST /api/v1/operations/maintenance/disable
```

## Escalation

- Primary: on-call rotation (Alertmanager)
- Secondary: platform engineering lead
- External: cloud provider support if infrastructure-related

## Post-Incident

1. Update incident record with root cause and timeline
2. Link to `backend/generated_release/` verification reports
3. Add action items to engineering backlog

## Related Docs

- `docs/RUNBOOK.md`
- `docs/DISASTER_RECOVERY.md`
- `/operations-runbooks`
