# DxCon Deployment Guide

## Environments

Use example env files as templates only:

- `backend/.env.example` — local development
- `backend/.env.staging.example` — staging
- `backend/.env.production.example` — production

Never commit real `.env` files.

## Required Production Settings

- `APP_ENV=production`
- `SECRET_KEY` and `JWT_SECRET_KEY` overridden from insecure defaults
- `DATABASE_URL` pointed at managed PostgreSQL
- `LOG_FORMAT=json`
- `CORS_ORIGINS` set to explicit allowed origins (not `*`)
- `STORAGE_PATH` or S3-compatible storage configuration

## Startup Sequence

1. Install dependencies from `backend/requirements.txt`
2. Export environment variables or mount env file securely
3. Run database migrations/readiness checks
4. Start via `backend/production_start.py` or container entrypoint
5. Verify health endpoints and smoke scripts

## Recommended Verification Before Cutover

```bash
python -m compileall backend/app backend/scripts backend/tests
python backend/scripts/verify_env_safety.py
python backend/scripts/verify_staging_stack.py
python backend/scripts/verify_enterprise_hardening_pack2.py
```

## Container Assets

- `backend/Dockerfile`
- `docker-compose.staging.yml`
- `docker-compose.production.yml`
- `deployment/nginx/`

## Rollback

Use generated rollback artifacts under `backend/generated_release/` and deployment rollback scripts documented in staging/production runbooks.

## Security Notes

- Keep secrets in platform secret stores, not git
- Exclude `venv/`, `instance/`, generated scratch paths, and local uploads temp dirs from version control
- Run security preflight before production promotion
