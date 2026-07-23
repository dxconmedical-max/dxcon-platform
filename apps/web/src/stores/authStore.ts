"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

import {
  AUTH_PERSIST_VERSION,
  AUTH_STORAGE_KEY,
  LEGACY_AUTH_STORAGE_KEYS,
  TRANSIENT_AUTH_KEYS,
  parseLoginResponse,
} from "@/lib/auth/session";
import { clearAuthCookies, setAuthCookies } from "@/lib/cookies";
import { workspacePathForRole } from "@/lib/roles";
import { decodeJwtPayload, isTokenExpired } from "@/lib/utils";
import { normalizeApiError, ApiError } from "@/lib/errors";
import {
  fetchCapabilities,
  fetchMe,
  login as loginRequest,
  logout as logoutRequest,
  refreshAccessToken,
  switchOrganization,
  type AuthCapabilities,
  type AuthUser,
  type Membership,
} from "@/services/auth";

export type AuthStatus =
  | "unauthenticated"
  | "authenticated"
  | "session_expired"
  | "forbidden"
  | "organization_required"
  | "workspace_required";

/**
 * Single-flight bootstrap lifecycle — never encoded as shared isLoading.
 *
 * idle → restoring → authenticated | anonymous | failed
 *
 * Protected routes MUST wait through idle/restoring.
 * Redirect only after terminal anonymous (or failed).
 */
export type BootstrapPhase =
  | "idle"
  | "restoring"
  | "authenticated"
  | "anonymous"
  | "failed";

export function isBootstrapPending(phase: BootstrapPhase): boolean {
  return phase === "idle" || phase === "restoring";
}

export function isBootstrapTerminal(phase: BootstrapPhase): boolean {
  return (
    phase === "authenticated" ||
    phase === "anonymous" ||
    phase === "failed"
  );
}

const SESSION_RESTORE_TIMEOUT_MS = 12_000;

type AuthState = {
  status: AuthStatus;
  bootstrapPhase: BootstrapPhase;
  user: AuthUser | null;
  role: string | null;
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: number | null;
  memberships: Membership[];
  activeOrganizationId: string | null;
  capabilities: AuthCapabilities | null;
  error: string | null;
  isHydrated: boolean;
  isInitializingSession: boolean;
  isSubmittingLogin: boolean;
  isRefreshingSession: boolean;

  setHydrated: (value: boolean) => void;
  clearError: () => void;
  clearTransientFlags: () => void;
  login: (
    email: string,
    password: string,
    remember?: boolean,
  ) => Promise<{ redirect: string }>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<AuthStatus>;
  selectOrganization: (organizationId: string) => Promise<string>;
  resolveAfterLogin: (remember?: boolean) => Promise<string>;
};

function tokenExpiry(accessToken: string | null): number | null {
  if (!accessToken) return null;
  const payload = decodeJwtPayload<{ exp?: number }>(accessToken);
  return payload?.exp ? payload.exp * 1000 : null;
}

async function withTimeout<T>(
  promise: Promise<T>,
  ms: number,
  label: string,
): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => {
          reject(new ApiError(`${label} timed out`, 408, { code: "TIMEOUT" }));
        }, ms);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

function clearLegacyStorage(): void {
  if (typeof sessionStorage === "undefined") return;
  for (const key of LEGACY_AUTH_STORAGE_KEYS) {
    try {
      sessionStorage.removeItem(key);
    } catch {
      // ignore
    }
  }
}

function isValidPersistedUser(value: unknown): value is AuthUser {
  if (!value || typeof value !== "object") return false;
  const u = value as Record<string, unknown>;
  return (
    typeof u.id === "string" &&
    u.id.length > 0 &&
    typeof u.email === "string" &&
    u.email.includes("@") &&
    typeof u.role === "string" &&
    u.role.length > 0
  );
}

export function migratePersistedAuth(
  persisted: unknown,
  _fromVersion?: number,
): Record<string, unknown> {
  clearLegacyStorage();
  if (!persisted || typeof persisted !== "object") {
    return {};
  }
  const raw = { ...(persisted as Record<string, unknown>) };
  for (const key of TRANSIENT_AUTH_KEYS) {
    delete raw[key];
  }
  delete raw.bootstrapPhase;

  const accessToken =
    typeof raw.accessToken === "string" && raw.accessToken.length > 0
      ? raw.accessToken
      : null;
  const refreshToken =
    typeof raw.refreshToken === "string" && raw.refreshToken.length > 0
      ? raw.refreshToken
      : null;
  const user = isValidPersistedUser(raw.user) ? raw.user : null;
  const role =
    typeof raw.role === "string" && raw.role.length > 0 ? raw.role : null;
  const tokenExpiresAt =
    typeof raw.tokenExpiresAt === "number" ? raw.tokenExpiresAt : null;
  const activeOrganizationId =
    typeof raw.activeOrganizationId === "string"
      ? raw.activeOrganizationId
      : null;

  if (!accessToken || !user) {
    return {};
  }

  return {
    accessToken,
    refreshToken,
    user,
    role: role ?? user.role,
    tokenExpiresAt,
    activeOrganizationId,
  };
}

export function sanitizePersistedAuth(persisted: unknown): Record<string, unknown> {
  return migratePersistedAuth(persisted);
}

export { AUTH_STORAGE_KEY, AUTH_PERSIST_VERSION };

/** Module-level single-flight promise — survives Strict Mode double-invoke. */
let restoreInFlight: Promise<AuthStatus> | null = null;

/** Test-only: clear in-flight restore between cases. */
export function resetAuthRestoreForTests(): void {
  restoreInFlight = null;
}

function patchChanged(
  set: (partial: Partial<AuthState>) => void,
  get: () => AuthState,
  partial: Partial<AuthState>,
): boolean {
  const current = get();
  const next: Partial<AuthState> = {};
  let changed = false;
  for (const [key, value] of Object.entries(partial) as [
    keyof AuthState,
    AuthState[keyof AuthState],
  ][]) {
    if (!Object.is(current[key], value)) {
      (next as Record<string, unknown>)[key as string] = value;
      changed = true;
    }
  }
  if (changed) set(next);
  return changed;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      status: "unauthenticated",
      bootstrapPhase: "idle",
      user: null,
      role: null,
      accessToken: null,
      refreshToken: null,
      tokenExpiresAt: null,
      memberships: [],
      activeOrganizationId: null,
      capabilities: null,
      error: null,
      isHydrated: false,
      isInitializingSession: false,
      isSubmittingLogin: false,
      isRefreshingSession: false,

      setHydrated: (value) => patchChanged(set, get, { isHydrated: value }),

      clearError: () => patchChanged(set, get, { error: null }),

      clearTransientFlags: () =>
        patchChanged(set, get, {
          isInitializingSession: false,
          isSubmittingLogin: false,
          isRefreshingSession: false,
          error: null,
        }),

      login: async (email, password, remember = false) => {
        if (get().isSubmittingLogin) {
          throw new ApiError("Login already in progress", 429, {
            code: "LOGIN_IN_PROGRESS",
          });
        }
        set({ isSubmittingLogin: true, error: null });
        try {
          const raw = await loginRequest(email, password);
          const session = parseLoginResponse(raw);
          set({
            accessToken: session.accessToken,
            refreshToken: session.refreshToken,
            user: session.user,
            role: session.role,
            tokenExpiresAt: tokenExpiry(session.accessToken),
            activeOrganizationId: session.user.organization_id ?? null,
          });
          const redirect = await get().resolveAfterLogin(remember);
          // Login path already bootstrapped — terminal authenticated so
          // AuthProvider does not start a second restoreSession.
          set({
            bootstrapPhase: "authenticated",
            isInitializingSession: false,
          });
          return { redirect };
        } catch (error) {
          const message = normalizeApiError(error);
          const status: AuthStatus =
            error instanceof ApiError && error.status === 403
              ? "forbidden"
              : "unauthenticated";
          set({ status, error: message, bootstrapPhase: "failed" });
          throw error;
        } finally {
          set({ isSubmittingLogin: false });
        }
      },

      resolveAfterLogin: async (remember = false) => {
        const { accessToken, user, role } = get();
        if (!accessToken || !user) {
          set({ status: "unauthenticated", bootstrapPhase: "failed" });
          return "/login";
        }
        const me = await fetchMe(accessToken);
        set({ memberships: me.memberships as Membership[] });

        if (
          me.requires_organization_selection ||
          (me.memberships.length > 1 && !me.active_organization_id)
        ) {
          set({ status: "organization_required" });
          return "/select-organization";
        }

        const orgId =
          me.active_organization_id ??
          (me.memberships[0] as Membership | undefined)?.organization_id ??
          null;
        let capabilities: AuthCapabilities;
        try {
          capabilities = await fetchCapabilities(accessToken, orgId);
        } catch {
          set({ status: "forbidden", error: "Unable to resolve permissions" });
          return "/forbidden";
        }

        // Capabilities payloads sometimes omit nested user — never leave nav
        // reading capabilities.user.role on undefined after a "successful" login.
        if (!capabilities.user) {
          capabilities = { ...capabilities, user };
        }

        set({
          capabilities,
          activeOrganizationId: orgId,
          status: "authenticated",
          // Same tick as status — otherwise login page useEffect navigates to
          // /app/admin while bootstrapPhase is still "anonymous" from hydrate,
          // and useRequireAuth immediately sends the user back to /login.
          bootstrapPhase: "authenticated",
        });
        setAuthCookies(role ?? user.role, orgId, remember);
        return capabilities.workspace || workspacePathForRole(role ?? user.role);
      },

      selectOrganization: async (organizationId) => {
        const { accessToken, role, user } = get();
        if (!accessToken) return "/login";
        set({ isInitializingSession: true });
        try {
          const capabilities = await switchOrganization(accessToken, organizationId);
          set({
            capabilities,
            activeOrganizationId: organizationId,
            status: "authenticated",
            bootstrapPhase: "authenticated",
          });
          setAuthCookies(role ?? user?.role ?? "", organizationId);
          return capabilities.workspace;
        } catch (error) {
          const message = normalizeApiError(error);
          set({ status: "forbidden", error: message, bootstrapPhase: "failed" });
          return "/forbidden";
        } finally {
          set({ isInitializingSession: false });
        }
      },

      logout: async () => {
        const refreshToken = get().refreshToken;
        if (refreshToken) {
          try {
            await logoutRequest(refreshToken);
          } catch {
            // proceed
          }
        }
        clearAuthCookies();
        clearLegacyStorage();
        try {
          useAuthStore.persist.clearStorage();
        } catch {
          // ignore
        }
        restoreInFlight = null;
        // Cleared session is terminal anonymous. Do NOT set phase to "idle" —
        // that re-triggers AuthProvider restore and leaves AppShell spinning.
        set({
          status: "unauthenticated",
          bootstrapPhase: "anonymous",
          user: null,
          role: null,
          accessToken: null,
          refreshToken: null,
          tokenExpiresAt: null,
          memberships: [],
          activeOrganizationId: null,
          capabilities: null,
          error: null,
          isInitializingSession: false,
          isSubmittingLogin: false,
          isRefreshingSession: false,
        });
      },

      restoreSession: () => {
        // Idempotent: share in-flight promise (Strict Mode safe).
        // NOTE: must NOT be an `async` function — that would wrap the shared
        // promise in a new outer Promise on every call (React #185 / dup work).
        if (restoreInFlight) {
          return restoreInFlight;
        }

        const state = get();

        // Already bootstrapped with a usable session — no store write.
        if (
          state.bootstrapPhase === "authenticated" &&
          state.status === "authenticated" &&
          state.capabilities &&
          state.accessToken
        ) {
          return Promise.resolve("authenticated" as AuthStatus);
        }

        const { accessToken, refreshToken, user } = state;
        if (!accessToken || !user) {
          patchChanged(set, get, {
            status: "unauthenticated",
            bootstrapPhase: "anonymous",
            isInitializingSession: false,
            isRefreshingSession: false,
          });
          return Promise.resolve("unauthenticated" as AuthStatus);
        }

        restoreInFlight = (async () => {
          set({
            bootstrapPhase: "restoring",
            isInitializingSession: true,
            error: null,
          });
          try {
            return await withTimeout(
              (async () => {
                let token = accessToken;
                if (isTokenExpired(token)) {
                  if (!refreshToken) {
                    await get().logout();
                    set({
                      status: "session_expired",
                      bootstrapPhase: "anonymous",
                    });
                    return "session_expired" as AuthStatus;
                  }
                  set({ isRefreshingSession: true });
                  try {
                    const refreshed = await refreshAccessToken(refreshToken);
                    const access =
                      refreshed.access_token ||
                      (refreshed as { token?: string }).token;
                    if (!access) {
                      throw new ApiError("Malformed refresh response", 502, {
                        code: "MALFORMED_REFRESH_RESPONSE",
                      });
                    }
                    token = access;
                    set({
                      accessToken: token,
                      tokenExpiresAt: tokenExpiry(token),
                    });
                  } catch {
                    await get().logout();
                    set({
                      status: "session_expired",
                      bootstrapPhase: "anonymous",
                    });
                    return "session_expired" as AuthStatus;
                  } finally {
                    set({ isRefreshingSession: false });
                  }
                }

                try {
                  const me = await fetchMe(token);
                  set({
                    memberships: me.memberships as Membership[],
                    user: me.user,
                    role: me.user.role,
                  });
                  if (me.requires_organization_selection) {
                    set({
                      status: "organization_required",
                      bootstrapPhase: "authenticated",
                    });
                    return "organization_required" as AuthStatus;
                  }
                  const orgId =
                    me.active_organization_id ??
                    (me.memberships[0] as Membership | undefined)
                      ?.organization_id ??
                    null;
                  let capabilities = await fetchCapabilities(token, orgId);
                  if (!capabilities.user) {
                    capabilities = { ...capabilities, user: me.user };
                  }
                  set({
                    capabilities,
                    activeOrganizationId: orgId,
                    status: "authenticated",
                    bootstrapPhase: "authenticated",
                    isInitializingSession: false,
                    error: null,
                  });
                  setAuthCookies(me.user.role, orgId);
                  return "authenticated" as AuthStatus;
                } catch (error) {
                  if (error instanceof ApiError && error.status === 401) {
                    await get().logout();
                    set({
                      status: "session_expired",
                      bootstrapPhase: "anonymous",
                      error: "Your session has expired. Please sign in again.",
                    });
                    return "session_expired" as AuthStatus;
                  }
                  if (error instanceof ApiError && error.status === 403) {
                    set({
                      status: "forbidden",
                      bootstrapPhase: "failed",
                      error: normalizeApiError(error),
                    });
                    return "forbidden" as AuthStatus;
                  }
                  set({
                    status: "unauthenticated",
                    bootstrapPhase: "failed",
                    error: normalizeApiError(error),
                  });
                  return "unauthenticated" as AuthStatus;
                }
              })(),
              SESSION_RESTORE_TIMEOUT_MS,
              "Session restore",
            );
          } catch (error) {
            console.debug("[authStore.restoreSession] failed/timeout", error);
            set({
              status: "unauthenticated",
              bootstrapPhase: "failed",
              error: normalizeApiError(error),
            });
            return "unauthenticated" as AuthStatus;
          } finally {
            set({
              isInitializingSession: false,
              isRefreshingSession: false,
            });
            restoreInFlight = null;
          }
        })();

        return restoreInFlight;
      },
    }),
    {
      name: AUTH_STORAGE_KEY,
      version: AUTH_PERSIST_VERSION,
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        role: state.role,
        tokenExpiresAt: state.tokenExpiresAt,
        activeOrganizationId: state.activeOrganizationId,
      }),
      migrate: (persisted, fromVersion) =>
        migratePersistedAuth(persisted, fromVersion),
      onRehydrateStorage: () => (state, error) => {
        // Hydration only — NEVER call restoreSession here (would recurse).
        if (error) {
          useAuthStore.setState({
            isHydrated: true,
            bootstrapPhase: "anonymous",
            isInitializingSession: false,
            isSubmittingLogin: false,
            isRefreshingSession: false,
            status: "unauthenticated",
            error: null,
          });
          return;
        }

        if (!state?.accessToken || !state.user) {
          // No persisted session — terminal anonymous. AuthProvider must NOT
          // treat this as "still restoring" and must NOT skip ahead from idle
          // without tokens (that previously used phase "complete" and caused
          // AppShell to redirect before any restore attempt when cookies alone
          // allowed the protected route).
          useAuthStore.setState({
            isHydrated: true,
            bootstrapPhase: "anonymous",
            isInitializingSession: false,
            isSubmittingLogin: false,
            isRefreshingSession: false,
            status: "unauthenticated",
            error: null,
          });
          return;
        }

        // Token present: AuthProvider is the sole owner that calls restoreSession.
        // Stay idle (pending) until restore finishes — never redirect yet.
        useAuthStore.setState({
          isHydrated: true,
          bootstrapPhase: "idle",
          isInitializingSession: true,
          isSubmittingLogin: false,
          isRefreshingSession: false,
          status: "unauthenticated",
          error: null,
        });
      },
    },
  ),
);
