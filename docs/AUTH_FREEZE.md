# Authentication Module Freeze

**Status:** PRODUCTION-STABLE (AUTH GATE 1 PASSED)  
**Runtime baseline:** `3176630`  
**Freeze tags:** `authentication-production-stable`, `auth-module-freeze`  
**Scope:** Frontend web authentication only. Do not modify runtime authentication under this freeze.

Gate 1 verified in production: login works, session restores, `/app/admin` renders, no redirect loop, no false “Redirecting to sign in…”.

---

## Frozen surfaces

### authStore
`apps/web/src/stores/authStore.ts`

Owns login, logout, `restoreSession`, `resolveAfterLogin`, persist (`dxcon-auth-v3` / sessionStorage), and `bootstrapPhase` transitions. Frozen — no casual refactors.

### AuthProvider
`apps/web/src/components/providers/AuthProvider.tsx`  
Wired from `apps/web/src/app/layout.tsx`

Sole owner that starts `restoreSession` when `bootstrapPhase === "idle"`. AppShell / route guards must not call restore on mount.

### useAuth
`apps/web/src/hooks/useAuth.ts` (`useAuth` export)

Field selectors over the store; exposes `isBootstrapping`, `isAuthenticated`, capabilities helpers. Do not reintroduce whole-store subscriptions.

### useRequireAuth
`apps/web/src/hooks/useAuth.ts` (`useRequireAuth` export)

Route guard only. Waits through pending bootstrap. Redirects only after terminal anonymous / session_expired — never while restoring, and never when `status === "authenticated"`.

### middleware auth
`apps/web/src/middleware.ts`

May require auth cookie for protected `/app/*` routes. Must **not** redirect `/login` → workspace based on cookie alone (avoids cookie/session mismatch loops).

### session bootstrap
`apps/web/src/lib/auth/session.ts`  
`apps/web/src/lib/auth/bootstrapDebug.ts`  
`apps/web/src/components/layout/AppShell.tsx`  
`apps/web/src/components/providers/AuthErrorBoundary.tsx`

Persist parse/migrate, bootstrap diagnostics, AppShell loading / diagnostic / shell render. AppShell must not show “Redirecting to sign in…” when the session is already authenticated.

### Supporting frozen paths
`apps/web/src/services/auth.ts`, `apps/web/src/lib/cookies.ts`, `apps/web/src/app/login/page.tsx`

---

## Session bootstrap state machine

```
idle → restoring → authenticated
                 → anonymous
                 → failed
```

1. Pending (`idle` / `restoring`, or not hydrated): wait — no login redirect.
2. Login success: set `status` and `bootstrapPhase` to authenticated in the **same** update.
3. Logout: terminal `anonymous` (not `idle`).
4. AuthProvider alone starts restore from `idle`.

---

## Redirect rules

| Condition | Action |
|-----------|--------|
| `bootstrapPhase` idle or restoring | Do not redirect |
| Terminal `anonymous` and not authenticated | `/login` |
| `session_expired` | `/login?reason=session-expired` |
| Authenticated (even if phase briefly stale `anonymous`) | Stay / render shell — **do not** redirect |
| Cookie present, no client session | Client owns outcome; middleware must not bounce login↔app on cookie alone |
| Authenticated + capabilities | Render workspace (e.g. `/app/admin`) |

---

## Mandatory CI regression tests

Locked by `.github/workflows/web-auth-ci.yml`:

- `npm run test:auth-freeze` (from `apps/web`)
- `npm run verify:auth-freeze` → `scripts/verify_auth_freeze.mjs`

Required suites:

- `src/app/login/page.test.tsx`
- `src/stores/authStore.login.test.ts`
- `src/components/providers/AuthProvider.test.tsx`
- `src/components/layout/AppShell.test.tsx`
- `src/components/layout/AdminBootstrap.integration.test.tsx`
- `src/hooks/useRequireAuth.bootstrap.test.tsx`
- `src/hooks/gate1Auth.regression.test.tsx`
- `src/lib/auth/session.test.ts`
- `src/services/api.auth.test.ts`
- `src/auth/e2e.login.hardening.test.ts` (offline; live probe only if `AUTH_LIVE_PROBE=1`)

---

## Regression approval required

**Any future auth change requires dedicated regression approval.**

PRs that touch frozen auth files or cookie/persist semantics must:

1. State that they break the Authentication freeze.
2. Pass `test:auth-freeze` + `verify:auth-freeze`.
3. Prove: anonymous → `/login`; authenticated → admin shell; logout → anonymous; no loop; no false Redirecting UI.
4. Not mix auth edits with unrelated product work.

Do not modify runtime authentication without that review.

---

## Out of scope

Backend auth APIs, CORS, DNS, CSP, Reception, Lab, and other product modules.
