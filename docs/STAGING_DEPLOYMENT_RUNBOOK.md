# Staging Deployment Runbook

**Release:** 8.1 · **Sprint:** 9

---

## Staging domains (preferred)

| Service | Domain |
| --- | --- |
| Public website | `uat.dxcon.com.vn` or `staging.dxcon.com.vn` |
| Application | `app.uat.dxcon.com.vn` or `app.staging.dxcon.com.vn` |
| API | `api.uat.dxcon.com.vn` or `api.staging.dxcon.com.vn` |

---

## Infrastructure separation (mandatory)

| Resource | Production | Staging |
| --- | --- | --- |
| Database | Render `dxcon-postgres` | **Separate** Postgres instance |
| Redis | Production Redis | **Separate** Redis instance |
| Backend service | `dxcon-api` (Render) | **Separate** Render service or staging config |
| Frontend | Vercel Production | Vercel Preview or separate staging project |
| File storage | Production uploads | Staging uploads path |
| PHI | Real (pilot) | **No real PHI** — synthetic data only |

**Never point staging to the production database.**

---

## Staging environment variables

### Frontend (Vercel staging/preview)

```
NEXT_PUBLIC_API_BASE_URL=https://api.uat.dxcon.com.vn
NEXT_PUBLIC_PUBLIC_SITE_URL=https://uat.dxcon.com.vn
NEXT_PUBLIC_APP_URL=https://app.uat.dxcon.com.vn
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_DEMO_MODE=false
```

> `DEMO_MODE=false` even in staging — use deterministic pilot accounts instead of demo auth.

### Backend (Render staging service)

```
APP_ENV=staging
DATABASE_URL=<staging-postgres-url>
REDIS_URL=<staging-redis-url>
CORS_ORIGINS=https://uat.dxcon.com.vn,https://www.uat.dxcon.com.vn,https://app.uat.dxcon.com.vn
SECRET_KEY=<staging-secret-min-32-chars>
JWT_SECRET_KEY=<staging-jwt-secret-min-32-chars>
SMTP_HOST=<staging-smtp-or-mailtrap>
SMTP_PORT=587
SMTP_USER=<user>
SMTP_PASSWORD=<secret>
SMTP_FROM=noreply@uat.dxcon.com.vn
SMTP_USE_TLS=true
DEMO_MODE=false
```

Test/simulator flags (`MOCK_TEST` payment adapter, AI `LOCAL` provider) are allowed **only** in staging.

---

## Deployment steps

### 1. Provision staging infrastructure

1. Create staging Postgres on Render (or separate provider).
2. Create staging Redis.
3. Create staging Render web service from `backend/render.yaml` template with staging env vars.
4. Create Vercel staging deployment (branch deploy or separate project).

### 2. Apply migrations (staging only)

```bash
# Connect to staging DB
psql $STAGING_DATABASE_URL -f backend/migrations/001_business_engine_sprint1.sql
# ... apply 002 through 020 in order
psql $STAGING_DATABASE_URL -f backend/migrations/020_patient_commerce.sql
```

See `docs/PRODUCTION_MIGRATION_RUNBOOK.md` for full list and verification queries.

### 3. Seed pilot accounts

Use deterministic staging accounts (no real PHI):

| Role | Email pattern | Purpose |
| --- | --- | --- |
| Admin | `admin@uat.dxcon.local` | Admin workspace UAT |
| Doctor | `doctor@uat.dxcon.local` | Doctor review UAT |
| Lab tech | `lab@uat.dxcon.local` | Technician validation UAT |
| Patient | `patient@uat.dxcon.local` | Patient booking/result UAT |
| Collector | `collector@uat.dxcon.local` | Collector workflow UAT |

Seed via existing demo seed script if available, or manual SQL insert.

### 4. Deploy frontend

```bash
# Vercel preview deploy from integration branch
vercel --prod  # or staging project
```

### 5. Verify staging

```bash
PUBLIC_SITE_URL=https://uat.dxcon.com.vn \
APP_URL=https://app.uat.dxcon.com.vn \
API_BASE_URL=https://api.uat.dxcon.com.vn \
node apps/web/scripts/production-smoke-test.mjs

python backend/scripts/production_api_smoke_test.py \
  --api-base https://api.uat.dxcon.com.vn \
  --cors-origin https://app.uat.dxcon.com.vn
```

### 6. Run manual UAT

Execute all cases in `docs/PRODUCTION_UAT_SPRINT_6_7.md` on staging.

---

## Staging label

The staging frontend should display a visible **STAGING** banner (implement if not present) to prevent confusion with production.

---

## Promotion to production

Only after:

- [ ] All staging smoke tests pass
- [ ] UAT-01 through UAT-16 pass on staging
- [ ] Migrations 016–020 verified on staging DB
- [ ] No Critical blockers in security report
- [ ] Operator confirms Vercel + Render production env vars

Then deploy integration branch to production Vercel + apply migrations to production DB (manual, with backup).
