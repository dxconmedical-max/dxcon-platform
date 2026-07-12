# Domain Routing

The `apps/web` Next.js application serves both the public marketing site and the authenticated pilot application from a single deployment.

## Host classification

| Host | Kind | Behavior |
|------|------|----------|
| `dxcon.com.vn` | Public site | Marketing pages; app paths redirect to `NEXT_PUBLIC_APP_URL` |
| `www.dxcon.com.vn` | Public site | 308 redirect to `dxcon.com.vn` |
| `app.dxcon.com.vn` | Application | Login, workspaces, marketplace |
| Other (e.g. Vercel preview) | Preview | All routes available without cross-domain redirect |

Implementation: `src/lib/domains.ts`, `src/middleware.ts`, `src/lib/urls.ts`.

## Public marketing routes

No authentication required:

- `/`
- `/services`
- `/partners`
- `/pricing`
- `/contact`
- `/book-demo`
- `/privacy`
- `/terms`

## Application routes

Session enforced via middleware cookie (`dxcon_authenticated`) and client-side `authStore`:

- `/login`, `/forgot-password`, `/reset-password`
- `/select-organization`
- `/session-expired`, `/forbidden`, `/service-unavailable`
- `/app` and workspace children (`/app/admin`, `/app/reception`, etc.)
- `/marketplace/*` (authenticated catalog flows)

## Cross-domain sign-in

When the marketing site is served from `dxcon.com.vn`, Sign In links use `NEXT_PUBLIC_APP_URL/login` so users authenticate on `app.dxcon.com.vn`.

On preview hosts, Sign In uses relative `/login` on the same deployment.

## Application path redirect

Requests to `dxcon.com.vn/app/*` (and other application prefixes) redirect to the same path on `app.dxcon.com.vn`. This keeps cookies and API calls on the application origin.

## Open redirect protection

Post-login `next` query parameters must be relative paths starting with `/`. Absolute URLs and `//` paths are rejected (`safeRedirectPath` in `src/lib/urls.ts`).

## Unknown workspace paths

Authenticated requests to unknown `/app/...` paths rewrite to `/app/not-found` instead of exposing arbitrary routes.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_PUBLIC_SITE_URL` | Canonical marketing origin |
| `NEXT_PUBLIC_APP_URL` | Application origin for sign-in and app redirects |

Do not hardcode Vercel preview hostnames; preview hosts are detected as neither public nor app production domains.
