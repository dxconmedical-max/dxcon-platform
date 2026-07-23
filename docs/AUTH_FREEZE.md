# Authentication Module Freeze

**Status:** PRODUCTION-VERIFIED AND FROZEN  
**Verified:** Authentication confirmed working in production (AUTH GATE 1).  
**Runtime baseline (no further runtime edits under this freeze):** `3176630`  
**Freeze documentation baseline:** `cbe047e` (initial freeze) — this document is the policy of record.  
**Freeze tags:** `authentication-production-stable`, `auth-module-freeze`  
**Scope:** Frontend web authentication only.

**Do not modify runtime authentication during Reception or any other product work.**  
Any auth change requires dedicated regression approval (see below).

---

## Frozen auth files

| Surface | Path |
|---------|------|
| authStore | `apps/web/src/stores/authStore.ts` |
| AuthProvider | `apps/web/src/components/providers/AuthProvider.tsx` |
| AuthErrorBoundary | `apps/web/src/components/providers/AuthErrorBoundary.tsx` |
| Root layout wiring | `apps/web/src/app/layout.tsx` |
| useAuth / useRequireAuth | `apps/web/src/hooks/useAuth.ts` |
| AppShell bootstrap UI | `apps/web/src/components/layout/AppShell.tsx` |
| middleware auth | `apps/web/src/middleware.ts` |
| Session migrate/parse | `apps/web/src/lib/auth/session.ts` |
| Bootstrap diagnostics | `apps/web/src/lib/auth/bootstrapDebug.ts` |
| Auth API client | `apps/web/src/services/auth.ts` |
| Auth cookies | `apps/web/src/lib/cookies.ts` |
| Login page | `apps/web/src/app/login/page.tsx` |

Supporting scripts (guards only; not runtime):

- `apps/web/scripts/verify_auth_freeze.mjs`
- `apps/web/package.json` scripts: `test:auth-freeze`, `verify:auth-freeze`
- `.github/workflows/web-auth-ci.yml`

---

## Approved auth state machine

```
idle → restoring → authenticated
                 → anonymous
                 → failed
```

Rules:

1. Pending (`idle` / `restoring`, or not hydrated): wait — never treat as anonymous for redirects.
2. Login success (`resolveAfterLogin`): set `status: "authenticated"` and `bootstrapPhase: "authenticated"` in the **same** store update.
3. Logout: terminal `anonymous` (not `idle`).
4. `AuthProvider` is the **sole** owner that starts `restoreSession` when `bootstrapPhase === "idle"`.
5. AppShell / `useRequireAuth` must **not** call `restoreSession` on mount.
6. Stale `bootstrapPhase: "anonymous"` while `status === "authenticated"` must **not** redirect; heal phase to `authenticated`.

---

## Session persistence strategy

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| Client session | Zustand `persist` → **sessionStorage** key `dxcon-auth-v3` | Survives refresh within the tab; cleared when the tab session ends |
| Persisted fields | `accessToken`, `refreshToken`, `user`, `role`, `tokenExpiresAt`, `activeOrganizationId` | Tokens + identity only — not bootstrap flags, not submit/loading flags |
| Migration | `migratePersistedAuth` / legacy key clear (`dxcon-auth`, `v1`, `v2`) | Prevents old loading/bootstrap state from reviving |
| Rehydrate | `onRehydrateStorage` sets `isHydrated`; does **not** call `restoreSession` | Avoids recursive restore |
| Middleware cookies | Presence cookies via `setAuthCookies` / `clearAuthCookies` (`AUTH_COOKIE`, role, org) | Soft gate for `/app/*`; **not** proof of a valid client session |
| Restore | AuthProvider → `restoreSession` (single-flight) after hydrate when phase is `idle` and tokens exist | Validates session with backend; sets terminal phase |

**Invariant:** Cookie alone must never bounce `/login` ↔ workspace. Client session + bootstrap phase own the outcome.

---

## Route-guard behavior

### `useRequireAuth` (client)

| Condition | Action |
|-----------|--------|
| Not hydrated, or `bootstrapPhase` idle/restoring | Wait — no redirect |
| `status === "session_expired"` | `/login?reason=session-expired` |
| Terminal `anonymous` **and** `status !== "authenticated"` | `/login` |
| `anonymous` phase **but** `status === "authenticated"` | Stay — skip stale phase (do not redirect) |
| `organization_required` | `/select-organization` |
| `forbidden` | `/forbidden` |
| Authenticated + capabilities | Allow workspace render |

### `AppShell`

| Condition | Action |
|-----------|--------|
| Bootstrapping (pending phase) | Loading spinner (bounded timeout → diagnostic) |
| Terminal anonymous **and** not authenticated | “Redirecting to sign in…” only |
| Authenticated (including brief stale anonymous phase) | Render shell — **never** false Redirecting UI |
| Authenticated without capabilities | Diagnostic (permissions not loaded) |

### `middleware.ts`

- May require auth cookie for protected `/app/*`.
- Must **not** redirect `/login` → workspace based on cookie alone.

---

## Mandatory regression tests (required CI)

Enforced by GitHub Actions workflow **`DxCon Web Auth Freeze CI`**  
Job / check name: **`auth-freeze-regression`**

This check **must** remain a required status check on `main` for PRs that touch `apps/web/**` or auth freeze docs/workflow.

Steps:

1. `node scripts/verify_auth_freeze.mjs` (`npm run verify:auth-freeze`)
2. `npm run test:auth-freeze`

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
- `src/auth/e2e.login.hardening.test.ts` (offline by default; live probe only if `AUTH_LIVE_PROBE=1`)

Prove on any freeze-breaking change: anonymous → `/login`; authenticated → admin shell; logout → anonymous; no redirect loop; no false Redirecting UI.

---

## Regression approval required

**Any future auth change requires dedicated regression approval.**

PRs that touch frozen auth files or cookie/persist semantics must:

1. State that they break the Authentication freeze.
2. Pass `test:auth-freeze` + `verify:auth-freeze`.
3. Not mix auth edits with Reception or other product work.
4. Leave runtime behavior unchanged unless the approved change is intentional and fully regression-covered.

Do not modify runtime authentication without that review.

---

## Out of scope

Backend auth APIs, CORS, DNS, CSP, Reception Phase 1+, Lab, Collector, and other product modules — none of these may edit frozen auth files under this freeze.
