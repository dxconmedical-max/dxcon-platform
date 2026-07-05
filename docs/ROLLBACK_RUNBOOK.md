# DxCon Rollback Runbook

## When to Rollback

- Failed deployment health checks after cutover
- Migration failure that cannot be forward-fixed within RTO
- Critical regression in orders, billing, or results pipeline
- Security preflight failure post-deploy

## Pre-Rollback

1. Enable maintenance: `POST /api/v1/operations/maintenance/enable`
2. Capture current state:
   - `GET /api/v1/system/version`
   - `GET /api/v1/system/build`
   - `GET /api/v1/operations/deployment/rollback-plan`
3. Notify on-call and stakeholders

## Rollback Procedure

### Application Rollback

1. Redeploy prior container tag (`BUILD_VERSION` from last known good release)
2. Use deployment pipeline:
   ```bash
   python deployment/pipeline/rollback.py
   ```
3. Hub reference: `/release-management/rollback`

### Database Rollback

If migration was applied and is reversible:

1. Run down-migration or restore from pre-deploy backup
2. Follow `docs/RESTORE_RUNBOOK.md` dry-run first

If migration is not reversible:

1. Restore database from pre-cutover validated backup
2. Accept data loss window per RPO

## Post-Rollback Validation

```bash
GET /api/v1/system/health
GET /api/v1/system/ready
python backend/scripts/final_ga_smoke.py
python backend/scripts/verify_release_management.py
```

## Artifacts

- `backend/generated_release/ROLLBACK_PACKAGE.json`
- `backend/generated_release/ROLLBACK_CHECKLIST.json`
- `deployment/pipeline/rollback.py`

## Communication Template

> Rollback initiated for DxCon [environment]. Reason: [summary]. ETA to restore: [time]. Current status: maintenance mode enabled.

## Related Docs

- `docs/DEPLOYMENT.md`
- `docs/DISASTER_RECOVERY.md`
- `/production-deployment/rollback`
