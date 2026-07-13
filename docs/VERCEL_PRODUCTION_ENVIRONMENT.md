# Vercel Production Environment Configuration

**Release:** 8.1 · **Sprint:** 9
**Project root directory:** `apps/web` (monorepo — set in Vercel dashboard)

---

## Required environment variables

Set these in **Vercel → Project → Settings → Environment Variables → Production**:

| Variable | Production value | Required |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://api.dxcon.com.vn` | ✅ |
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | `https://dxcon.com.vn` | ✅ |
| `NEXT_PUBLIC_APP_URL` | `https://app.dxcon.com.vn` | ✅ |
| `NEXT_PUBLIC_APP_ENV` | `production` | ✅ |
| `NEXT_PUBLIC_DEMO_MODE` | `false` | ✅ |

**Do not commit secrets.** These are all public (`NEXT_PUBLIC_*`) and safe to document.

---

## Build-time validation (automatic)

`apps/web/next.config.ts` **fails the production build** if:

- Any of the four required vars is missing
- `NEXT_PUBLIC_DEMO_MODE=true`

`apps/web/src/lib/env.ts` **throws at module load** in production if:

- Any required var is missing
- `DEMO_MODE=true`
- Any URL points to `localhost`, `127.0.0.1`, or `*.local`

---

## Vercel project settings

| Setting | Value |
| --- | --- |
| Framework Preset | Next.js |
| Root Directory | `apps/web` |
| Build Command | `npm run build` (default) |
| Output Directory | `.next` (default) |
| Install Command | `npm ci` or `npm install` |
| Node.js Version | 20.x (recommended) |

---

## Domains (Vercel → Settings → Domains)

| Domain | Purpose |
| --- | --- |
| `dxcon.com.vn` | Public website (apex) |
| `www.dxcon.com.vn` | Redirects to apex (middleware 308) |
| `app.dxcon.com.vn` | Application (auth + workspaces) |

See `docs/APP_SUBDOMAIN_DNS.md` for DNS setup steps.

---

## Preview deployments

Preview deployments use Vercel-assigned `*.vercel.app` hostnames. These are treated as `preview` hosts by `apps/web/src/lib/domains.ts` — all routes (public + app) are served on the same preview host for testing. No hardcoded preview hostname is required.

---

## Verification after deploy

```bash
# From repo root
node apps/web/scripts/production-smoke-test.mjs
```

Or with explicit overrides:

```bash
PUBLIC_SITE_URL=https://dxcon.com.vn \
APP_URL=https://app.dxcon.com.vn \
API_BASE_URL=https://api.dxcon.com.vn \
node apps/web/scripts/production-smoke-test.mjs
```

---

## Common failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| Build fails immediately | Missing env var | Add all five vars in Vercel Production |
| Build fails "localhost" | API URL points to localhost | Set `NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn` |
| Sign In goes to wrong host | `NEXT_PUBLIC_APP_URL` wrong | Set to `https://app.dxcon.com.vn` |
| `/app` accessible without login on public host | Middleware not running | Confirm Root Directory is `apps/web` |
