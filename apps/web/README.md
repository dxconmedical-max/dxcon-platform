# DxCon Web — Production Frontend

Official DxCon production frontend built with **Next.js**, **TypeScript**, **Tailwind CSS**, and the **App Router**.

Connects to the production API at `https://api.dxcon.com.vn` — no mock backend.

## Architecture

```
apps/web/src/
  app/           # Routes (landing, login, workspaces)
  components/    # UI, layout, landing sections
  hooks/         # Auth hooks
  services/      # API client + auth service
  stores/        # Zustand auth store
  lib/           # Roles, constants, utilities
  styles/        # Global styles
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Public landing page |
| `/login` | Unified login gateway |
| `/app` | Default workspace |
| `/admin` | Administration |
| `/doctor` | Doctor workspace |
| `/patient` | Patient portal |
| `/lab` | Laboratory |
| `/collector` | Home collection |
| `/clinic` | Clinic operations |

## Environment

Copy `.env.example` to `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn
```

## Development

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Production build

```bash
npm run build
npm run start
```

## Deploy — Vercel

1. Import the repository and set root directory to `apps/web`.
2. Framework preset: **Next.js**.
3. Environment variable: `NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn`
4. Add custom domains: `dxcon.com.vn`, `www.dxcon.com.vn`, `app.dxcon.com.vn`.

## Deploy — Render Static Site / Web Service

**Web service (recommended for SSR):**

- Root directory: `apps/web`
- Build: `npm install && npm run build`
- Start: `npm run start`

**Static export** is not configured by default; use the Node server for auth middleware and protected routes.

## Authentication

- `POST /api/v1/auth/login` — email + password
- `POST /api/v1/auth/refresh` — refresh token placeholder (implemented)
- `POST /api/v1/auth/logout` — revoke refresh token
- JWT stored in Zustand + localStorage; session cookie for middleware
- Role-based redirect after login (see `src/lib/roles.ts`)

## API layer

- `src/services/api.ts` — shared fetch client with JWT, error normalization, network handling
- `src/services/auth.ts` — login, refresh, logout

## Release 2.0 — Epic 1

Production Frontend Foundation for DxCon. Backend remains at `api.dxcon.com.vn`.
