# Staging Environment Variables — Release 8.1

**Do not commit secrets. Copy values from Render/Vercel dashboards.**

---

## Frontend (Vercel staging project)

| Variable | Staging value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://api-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | `https://staging.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_URL` | `https://app-staging.dxcon.com.vn` |
| `NEXT_PUBLIC_APP_ENV` | `staging` |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |

Build fails if any required var missing or points to localhost.

---

## Backend (Render staging service)

| Variable | Required | Staging notes |
|---|---|---|
| `APP_ENV` | ✅ | `staging` |
| `DATABASE_URL` | ✅ | **Separate** staging Postgres (never production) |
| `REDIS_URL` | ✅ | **Separate** staging Redis |
| `SECRET_KEY` | ✅ | Generate unique 32+ char secret |
| `JWT_SECRET_KEY` | ✅ | Generate unique 32+ char secret |
| `CORS_ORIGINS` | ✅ | `https://staging.dxcon.com.vn,https://app-staging.dxcon.com.vn` |
| `SMTP_HOST` | ✅ for mail | Mailtrap or safe capture provider |
| `SMTP_PORT` | ✅ | `587` |
| `SMTP_USER` | ✅ | From provider |
| `SMTP_PASSWORD` | ✅ | From provider (secret) |
| `SMTP_FROM` | ✅ | `noreply@staging.dxcon.local` |
| `SMTP_USE_TLS` | ✅ | `true` |
| `DEMO_MODE` | ✅ | `false` |
| `LOG_FORMAT` | ✅ | `json` |
| `MARKETPLACE_PAYMENT_WEBHOOK_SECRET` | Optional | Staging-only webhook secret |

**Do not** include production origins in staging `CORS_ORIGINS`.
**Do not** point staging at production database or Redis.

---

## Validation guards (code)

| Guard | Location |
|---|---|
| Wildcard CORS blocked in strict env | `production_readiness.validate_cors` |
| SQLite blocked in staging/production | `production_readiness.validate_database` |
| Redis required in production | `production_readiness.check_redis_health` |
| SMTP required in production | `production_readiness` SMTP check |
| Weak default secrets flagged | `config_validation.INSECURE_DEFAULTS` |
| Frontend localhost URL rejection | `apps/web/src/lib/env.ts` |
| Payment mock adapter blocked in strict env | `payment_adapters.get_payment_adapter` |

---

## Manual checklist (fill after resource creation)

### Render staging service
- [ ] Service name: `________________`
- [ ] Service URL: `________________`
- [ ] Git branch: `release/8.1-production-integration`
- [ ] Health check: `/api/v1/system/health`

### Render staging Postgres
- [ ] Database name: `________________`
- [ ] Internal connection string copied to `DATABASE_URL`

### Render staging Redis
- [ ] Redis URL copied to `REDIS_URL`

### Vercel staging
- [ ] Project name: `________________`
- [ ] Root directory: `apps/web`
- [ ] Domains attached: `staging.dxcon.com.vn`, `app-staging.dxcon.com.vn`

### DNS (from provider dashboards — do not invent)
- [ ] `staging.dxcon.com.vn` → Vercel target: `________________`
- [ ] `app-staging.dxcon.com.vn` → Vercel target: `________________`
- [ ] `api-staging.dxcon.com.vn` → Render target: `________________`
