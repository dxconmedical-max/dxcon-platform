# Frontend Contract Freeze — Release 2.0

**App:** `apps/web` (Next.js)  
**Target domain:** https://app.dxcon.com.vn

## Capability payload (from `/api/v1/auth/capabilities`)

```typescript
{
  user: { id, email, role },
  organization: { id, name },
  membership: { id, role },
  workspace: string,
  roles: string[],
  permissions: string[],
  scopes: string[],
  features: string[],
  token_expires_at: string
}
```

## Auth flow

1. Login → store tokens in sessionStorage
2. Load capabilities on app shell mount
3. Middleware protects `/app/*`
4. Org switch → refresh capabilities

## Workspace routes

`/app/admin`, `/app/doctor`, `/app/patient`, `/app/lab`, `/app/collector`, `/app/clinic`, `/app/reception`, `/app/executive`

## Rules

1. UI permission checks mirror backend but do not replace them.
2. No demo mode in production builds.
3. Security headers configured in `next.config.ts`.

## Verification

`apps/web/generated-release/FRONTEND_CONTRACT_FREEZE_REPORT.json`
