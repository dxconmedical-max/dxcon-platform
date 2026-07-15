# Vercel Staging Setup — Release 9.0

Derived from `apps/web/package.json`, `apps/web/next.config.ts`, `apps/web/src/middleware.ts`, `apps/web/src/lib/domains.ts`.

---

## Project configuration

| Field | Value |
|---|---|
| Framework | Next.js |
| Root Directory | `apps/web` |
| Branch | `release/8.1-production-integration` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output | Next.js default (`.next`) |
| Node | 20.x recommended |

Use a **dedicated staging project** or a branch environment clearly labelled STAGING. Do not reuse production env vars.

---

## Environment variables

```text
NEXT_PUBLIC_API_BASE_URL=https://api-staging.dxcon.com.vn
NEXT_PUBLIC_PUBLIC_SITE_URL=https://staging.dxcon.com.vn
NEXT_PUBLIC_APP_URL=https://app-staging.dxcon.com.vn
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_DEMO_MODE=false
```

Build fails if required vars missing, `DEMO_MODE=true`, or URLs are localhost (`next.config.ts` + `env.ts`).

---

## Domains

Add in Vercel → Domains (copy DNS targets after add):

| Domain | Purpose |
|---|---|
| `staging.dxcon.com.vn` | Public marketing site |
| `app-staging.dxcon.com.vn` | Login + `/app/*` workspaces |

Middleware (`domains.ts`) treats:

- `staging.dxcon.com.vn` as public site  
- `app-staging.dxcon.com.vn` as application host  

Sign In on public staging opens `https://app-staging.dxcon.com.vn/login`.

### Served application routes (app host)

`/login`, `/register`, `/forgot-password`, `/reset-password`, `/select-organization`, `/session-expired`, `/forbidden`, `/service-unavailable`, `/app`, `/app/admin`, `/app/executive`, `/app/reception`, `/app/doctor`, `/app/clinic`, `/app/lab`, `/app/collector`, `/app/patient`

Public landing remains on `staging.dxcon.com.vn` (`/`, `/services`, `/partners`, …).

---

## Redeploy / verify

1. Push to branch → Auto Deploy  
2. Confirm build green  
3. Open `https://staging.dxcon.com.vn` → 200  
4. Open `https://app-staging.dxcon.com.vn/login` → 200  
5. Unauthenticated `/app` → redirect to login  
6. Confirm amber **STAGING** banner after login  

```bash
PUBLIC_SITE_URL=https://staging.dxcon.com.vn \
APP_URL=https://app-staging.dxcon.com.vn \
API_BASE_URL=https://api-staging.dxcon.com.vn \
SMOKE_ENV=staging \
node apps/web/scripts/staging-smoke-test.mjs
```
