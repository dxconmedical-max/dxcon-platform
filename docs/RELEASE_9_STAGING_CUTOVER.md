# Release 9.0 — Staging Cutover

**Branch:** `release/8.1-production-integration`  
**Goal:** Deploy the Release 8.1 tip to an isolated staging stack and prove smoke + UAT before production.

---

## Prerequisites

- [ ] Staging Postgres created (not production)
- [ ] Staging Redis created (not production)
- [ ] Staging Render web service created
- [ ] Staging Vercel project/env configured (`apps/web` root)
- [ ] Staging env vars set per `docs/RELEASE_9_STAGING_ENVIRONMENT.md`
- [ ] No real PHI seeded

---

## Deployment sequence

1. **Attach staging Postgres + Redis** to the staging Render service.
2. **Set staging env vars** (including staging-only `CORS_ORIGINS`).
3. **Deploy backend** from `release/8.1-production-integration`.
4. **Backup staging DB**, then apply migrations **016→020** in order (`docs/RELEASE_9_MIGRATION_EXECUTION_PLAN.md`).
5. **Verify** backend health: `https://api-staging.dxcon.com.vn/api/v1/system/health` → 200.
6. **Add domains in Vercel**: `staging.dxcon.com.vn`, `app-staging.dxcon.com.vn`.
7. **Copy DNS targets from Vercel**; create Cloudflare records as **DNS only**.
8. **Add `api-staging.dxcon.com.vn`** in Render Custom Domains; copy the exact DNS target shown.
9. **Wait for TLS** certificates on all three hosts.
10. **Deploy frontend** with staging `NEXT_PUBLIC_*` values.
11. **Run smoke tests:**

```bash
PUBLIC_SITE_URL=https://staging.dxcon.com.vn \
APP_URL=https://app-staging.dxcon.com.vn \
API_BASE_URL=https://api-staging.dxcon.com.vn \
SMOKE_ENV=staging \
SMOKE_REPORT_PATH=generated-release/RELEASE_9_STAGING_SMOKE_REPORT.json \
node apps/web/scripts/production-smoke-test.mjs

python backend/scripts/production_api_smoke_test.py \
  --api-base https://api-staging.dxcon.com.vn \
  --cors-origin https://app-staging.dxcon.com.vn \
  --report generated-release/RELEASE_9_STAGING_SMOKE_REPORT.json
```

12. **Execute UAT** in `docs/PRODUCTION_UAT_SPRINT_6_7.md` (staging URLs).
13. Only then proceed to `docs/RELEASE_9_PRODUCTION_CUTOVER.md`.

---

## Isolation rules

| Must stay separate | Production | Staging |
|---|---|---|
| Database | prod | staging |
| Redis | prod | staging |
| Backend service | prod | staging |
| Frontend deployment | prod | staging |
| CORS origins | prod hosts only | staging hosts only |
| Payment secrets | live | test / disabled |
| PHI | pilot policy | synthetic only |

---

## DNS note

Never invent Vercel/Render CNAME or A-record targets. After adding each domain, the provider UI shows the exact value to paste into Cloudflare. Keep proxy **DNS only** until HTTPS verifies.
