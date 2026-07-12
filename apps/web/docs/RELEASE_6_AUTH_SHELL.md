# Release 6.0 — Authentication + Application Shell + Role Workspace

Branch: `release/6.0-auth-shell`

## Scope

Transforms the deployed Next.js site into a production pilot application shell with:

1. **Authentication** — JWT login, refresh, logout, organization selection, capabilities
2. **Application shell** — Sidebar, header, mobile navigation, session restore
3. **Role workspaces** — Eight role routes wired to verified backend dashboard APIs

## Authentication flow

```
/login → POST /api/v1/auth/login
       → GET /api/v1/auth/me
       → GET /api/v1/auth/capabilities
       → redirect to capabilities.workspace (e.g. /app/reception)

/select-organization → POST /api/v1/auth/switch-organization

/app → redirects to role workspace home
```

Session tokens persist in `sessionStorage`. Middleware uses `dxcon_authenticated` cookie for route protection.

## Role workspaces

| Route | Permission | Dashboard API |
|-------|------------|-----------------|
| `/app/admin` | `users.read` | `GET /api/v1/dashboard/admin` |
| `/app/executive` | `executive.read` | `GET /api/v1/executive-platform/dashboard` |
| `/app/reception` | `reception.read` | `GET /api/v1/reception/workspace/dashboard` |
| `/app/doctor` | `portal.doctor.read` | `GET /api/v1/portal/doctor/dashboard` |
| `/app/lab` | `lab.read` | `GET /api/v1/lab/workspace/dashboard` |
| `/app/collector` | `collections.read` | `GET /api/v1/dashboard/collector` |
| `/app/clinic` | `data.view` | `GET /api/v1/clinic/dashboard` |
| `/app/patient` | `portal.patient.read` | `GET /api/v1/portal/patient/dashboard` |

Dashboard metrics load client-side after authentication. Failed API calls show a warning with placeholder values — no fabricated production statistics.

## Key modules

| Path | Role |
|------|------|
| `src/lib/workspaces.ts` | Workspace registry and KPI extractors |
| `src/hooks/useWorkspaceDashboard.ts` | Authenticated dashboard fetch hook |
| `src/components/layout/RoleWorkspace.tsx` | Shared role workspace page |
| `src/components/layout/AppShell.tsx` | Application chrome with mobile drawer |
| `src/components/providers/AuthProvider.tsx` | Session restore on `/app` routes |

## Verification

```bash
cd apps/web
npm run lint
npm run typecheck
npm run test
npm run verify:release-6
npm run build
```

Report: `generated-release/RELEASE_6_AUTH_SHELL_REPORT.json`
