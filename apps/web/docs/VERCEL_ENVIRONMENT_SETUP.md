# Vercel environment setup

Root directory: `apps/web`  
Framework: **Next.js**

## Required variables (Production + Preview)

```
NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn
NEXT_PUBLIC_PUBLIC_SITE_URL=https://dxcon.com.vn
NEXT_PUBLIC_APP_URL=https://app.dxcon.com.vn
NEXT_PUBLIC_APP_ENV=production
NEXT_PUBLIC_DEMO_MODE=false
```

Production builds **fail** if any required variable is missing or if `NEXT_PUBLIC_DEMO_MODE` is not `false`.

## Local development

Copy `apps/web/.env.example` to `apps/web/.env.local` and uncomment development overrides.

## Preview deployments

Vercel preview domains are treated as **preview hosts** — both marketing and application routes work on the same deployment without cross-domain redirects.

## Verification

```bash
cd apps/web
npm run build   # with production env vars set
npm run verify:production-pilot
```

See also [VERCEL_PRODUCTION_CONFIGURATION.md](./VERCEL_PRODUCTION_CONFIGURATION.md).
