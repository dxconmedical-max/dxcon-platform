# Vercel Production Configuration

## Project settings

| Setting | Value |
|---------|-------|
| Framework | Next.js |
| Root directory | `apps/web` |
| Build command | `npm run build` (default) |
| Install command | `npm install` (from `apps/web`) |
| Output | Next.js default |

## Required environment variables

Set these in the Vercel project for **Production** and **Preview** environments:

```
NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn
NEXT_PUBLIC_PUBLIC_SITE_URL=https://dxcon.com.vn
NEXT_PUBLIC_APP_URL=https://app.dxcon.com.vn
NEXT_PUBLIC_APP_ENV=production
NEXT_PUBLIC_DEMO_MODE=false
```

The production build **fails** if any required variable is missing or if `NEXT_PUBLIC_DEMO_MODE` is not `false`.

## Domain mapping

| Domain | Role |
|--------|------|
| `dxcon.com.vn` | Public marketing site |
| `www.dxcon.com.vn` | Redirects to `dxcon.com.vn` |
| `app.dxcon.com.vn` | Authentication and workspaces |
| `*.vercel.app` (preview) | Both marketing and app routes (no hostname split) |

Configure all production domains on the same Vercel project pointing to `apps/web`.

## Backend CORS

Ensure the API `CORS_ORIGINS` includes:

- `https://dxcon.com.vn`
- `https://www.dxcon.com.vn`
- `https://app.dxcon.com.vn`
- Vercel preview origins during rollout (e.g. `https://<project>-<branch>.vercel.app`)

## Security headers

CSP `connect-src` is derived from `NEXT_PUBLIC_API_BASE_URL` in `next.config.ts`.

## Local development

Copy `.env.example` to `.env.local` and uncomment development overrides. Do not commit `.env.local`.

## Verification

```bash
cd apps/web
npm run lint
npm run typecheck
npm run test
NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn \
NEXT_PUBLIC_PUBLIC_SITE_URL=https://dxcon.com.vn \
NEXT_PUBLIC_APP_URL=https://app.dxcon.com.vn \
NEXT_PUBLIC_APP_ENV=production \
NEXT_PUBLIC_DEMO_MODE=false \
npm run build
npm run verify
node scripts/verify_production_web.mjs
```
