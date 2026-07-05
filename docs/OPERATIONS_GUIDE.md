# DxCon Operations Guide — Enterprise v1.0

## Daily Operations

1. Check **Monitoring Center** at `/monitoring-center` for application, queue, database, and Redis health.
2. Review **Executive Metrics** at `/executive-metrics` for business KPIs.
3. Monitor **AI Operations** at `/ai-operations` for inference failures and cost trends.
4. Confirm backup jobs in **Backup & Recovery** at `/backup-recovery`.

## Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /live` | Liveness probe |
| `GET /ready` | Readiness probe |
| `GET /api/v1/system/health` | Full health payload |
| `GET /api/v1/system/liveness` | API liveness |

Run local health check:

```bash
cd backend
python scripts/health_check.py
```

## Incident Response

1. Open Monitoring Center alerts overview.
2. Follow [INCIDENT_RUNBOOK.md](INCIDENT_RUNBOOK.md).
3. Escalate via Security & Compliance hub if PHI exposure suspected.

## Scheduled Jobs

- Database backup: `backup.database` (recommended cron `0 2 * * *`)
- Trigger manual backup: `POST /api/v1/operations/backups/run`

## Roles

| Role | Primary hubs |
|------|--------------|
| SUPER_ADMIN | All enterprise hubs |
| ADMIN | Operations, release, security |
| DOCTOR | Clinical, AI, patient results |
| RECEPTION | Orders, patients, billing |

## See Also

- [RUNBOOK.md](RUNBOOK.md)
- [OPERATIONS.md](OPERATIONS.md) — legacy operations reference
- [GO_LIVE_RUNBOOK.md](GO_LIVE_RUNBOOK.md)
