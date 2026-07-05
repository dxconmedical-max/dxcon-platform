# Deployment Architecture — Phase 9

## Overview

DxCon supports multi-cloud and on-premise deployment through a cloud abstraction layer that maps regional requirements to provider-specific services.

## Cloud Providers

| Provider | Status | Primary services |
|----------|--------|------------------|
| AWS | READY | RDS, S3, EKS, CloudWatch |
| Azure | READY | PostgreSQL, Blob, AKS, Monitor |
| Google Cloud | READY | Cloud SQL, GCS, GKE, Operations |
| Render | READY | Web Service, PostgreSQL, Redis |
| On-premise | READY | Docker, Kubernetes, bare metal |

## Deployment Stack

```
Internet
   │
   ▼
 Nginx (TLS termination)
   │
   ▼
 Gunicorn / Flask API
   │
   ├── PostgreSQL (primary + read replica scaffold)
   ├── Redis (cache / queue)
   └── Worker / Scheduler
```

## Regional Deployment Pattern

1. Select target region (VN, US, EU, SG)
2. Apply locale, timezone, currency, and tax profile
3. Deploy via cloud abstraction layer (provider-specific manifest)
4. Configure geo-replication scaffold for read replicas
5. Enable multi-region backup schedule
6. Validate disaster recovery runbook

## Assets

Production deployment assets are validated via `production_deployment_service`:

- `backend/Dockerfile`
- `docker-compose.production.yml`
- `deployment/kubernetes/deployment.yaml`
- `deployment/nginx/nginx.conf`
- Health probes: `/live`, `/ready`, `/api/v1/system/health`

## Multi-region Backup

- Primary backup: `backup.database` scheduled job
- DR secondary region: scaffold (async replication)
- API trigger: `POST /api/v1/operations/backups/run`

## Disaster Recovery

| Metric | Target |
|--------|--------|
| RTO | 60 minutes |
| RPO | 15 minutes |

Runbook: `backup_recovery_service.disaster_recovery_runbook()`

## Reports

- `REGIONAL_READINESS_REPORT.json` — module and region readiness
- `DEPLOYMENT_REPORT.json` — cloud providers, backup, DR status
