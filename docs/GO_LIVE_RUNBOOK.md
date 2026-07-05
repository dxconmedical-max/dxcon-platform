# DxCon Go-Live Runbook

## Pre-Cutover Checklist

1. Confirm staging sign-off: `backend/scripts/verify_staging_stack.py`
2. Run enterprise hardening: `backend/scripts/verify_enterprise_hardening_pack10.py`
3. Verify migrations: `GET /api/v1/system/readiness`
4. Confirm backup completed: `GET /api/v1/operations/backups`
5. Review release notes: `/release-management/notes`
6. Confirm pilot status: `/pilot-status`

## Cutover Steps

1. Enable maintenance window: `POST /api/v1/operations/maintenance/enable`
2. Deploy production container with `LOG_FORMAT=json` and production env
3. Run database migrations if required
4. Verify health probes:
   - `GET /api/v1/system/health`
   - `GET /api/v1/system/ready`
   - `GET /api/v1/system/live`
5. Run smoke test: `backend/scripts/final_ga_smoke.py`
6. Disable maintenance: `POST /api/v1/operations/maintenance/disable`

## Post Go-Live Validation

- `/executive-v9` — executive dashboard loads
- `/monitoring` — no critical alerts
- `/pilot-status` — clinics, labs, collectors online
- `/production-deployment/readiness` — deployment score OK

## Rollback Trigger

Rollback if any of the following occur within 30 minutes of cutover:

- Health endpoints not OK for 5 consecutive minutes
- Error rate above 5% on critical API routes
- Database migration failure
- Payment or order pipeline blocked

See `docs/ROLLBACK_RUNBOOK.md`.

## Contacts

- On-call: Alertmanager route in `deployment/monitoring/alertmanager/alertmanager.yml`
- Incident process: `docs/INCIDENT_RUNBOOK.md`

## Artifacts

- `backend/generated_release/GO_LIVE_BLOCKERS.json`
- `backend/generated_release/RC1_REPORT.json`
- `backend/generated_release/PRODUCTION_DEPLOYMENT_REPORT.json`
