# DxCon Operations Runbook

## Daily Checks

1. `/api/v1/system/health` — status OK
2. `/api/v1/system/ready` — readiness OK
3. Prometheus alerts — no critical firing
4. Backup job recency — `GET /api/v1/operations/backups`

## Deploy

1. Run `backend/scripts/verify_enterprise_hardening_pack10.py`
2. Deploy container with `LOG_FORMAT=json`
3. Verify `/api/v1/system/version` and `/api/v1/system/build`
4. Run smoke: `backend/scripts/final_ga_smoke.py` or staging equivalent

## Incident Triage

1. Collect `request_id` / correlation ID from logs
2. Check `backend/generated_release/operations_review.json`
3. Review Grafana dashboard `deployment/monitoring/grafana/dashboards/dxcon-overview.json`
4. Escalate per on-call rotation

## Maintenance Window

```bash
POST /api/v1/operations/maintenance/schedule
POST /api/v1/operations/maintenance/enable
# perform work
POST /api/v1/operations/maintenance/disable
```

## Enterprise Verification

```bash
cd backend
./venv/bin/python scripts/verify_enterprise_hardening_pack5.py
./venv/bin/python scripts/verify_enterprise_hardening_pack10.py
```
