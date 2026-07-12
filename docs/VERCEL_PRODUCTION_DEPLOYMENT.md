# Vercel production deployment

## Project

| Setting | Value |
|---------|-------|
| Framework | Next.js |
| Root Directory | `apps/web` |
| Production API | `https://api.dxcon.com.vn` |

## Environment variables

Set in Vercel → Project → Settings → Environment Variables:

```
NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn
NEXT_PUBLIC_PUBLIC_SITE_URL=https://dxcon.com.vn
NEXT_PUBLIC_APP_URL=https://app.dxcon.com.vn
NEXT_PUBLIC_APP_ENV=production
NEXT_PUBLIC_DEMO_MODE=false
```

## Domains

| Domain | Purpose |
|--------|---------|
| `dxcon.com.vn` | Public marketing site |
| `www.dxcon.com.vn` | Redirect to apex |
| `app.dxcon.com.vn` | Login and workspaces |

Add domains in Vercel → Project → Domains. Use the **exact DNS records** Vercel provides during domain setup (do not invent targets).

## Deploy

1. Push `release/6.0-auth-shell` (or merged `main`) to GitHub
2. Vercel auto-builds `apps/web`
3. Verify build logs show production env validation pass
4. Run [PRODUCTION_SMOKE_TEST.md](./PRODUCTION_SMOKE_TEST.md)

## Manual actions after deploy

- Configure API `CORS_ORIGINS` — see [PRODUCTION_CORS_SETUP.md](./PRODUCTION_CORS_SETUP.md)
- Map Cloudflare DNS — see [CLOUDFLARE_WEB_DNS.md](./CLOUDFLARE_WEB_DNS.md)
- Create pilot accounts on staging — see [PILOT_ACCOUNT_SETUP.md](./PILOT_ACCOUNT_SETUP.md)
