# Deployment Runbook

```bash
docker compose -f docker-compose.production.yml up -d --build
python backend/scripts/apply_migrations.py
python backend/scripts/verify_production_readiness.py
```
