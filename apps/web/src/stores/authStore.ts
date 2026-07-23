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

/**
 * Domain session status — never encode submit/init/refresh loading here.
 * Loading is represented only by the explicit boolean flags below.
 */
export type AuthStatus =
  | "unauthenticated"
  | "authenticated"
  | "session_expired"
  | "forbidden"
  | "organization_required"
  | "workspace_required";

const SESSION_RESTORE_TIMEOUT_MS = 12_000;

type AuthState = {
  status: AuthStatus;
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
  /** Persist/rehydrate + restoreSession in progress. */
  isInitializingSession: boolean;
  /** Login form submit in progress — only flag the Sign in button may use. */
  isSubmittingLogin: boolean;
  /** Token refresh in progress. */
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

/**
 * Persist migration: strip every transient/loading field and keep only a
 * structurally valid session snapshot.
 */
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

  // Discard incomplete / incompatible snapshots entirely.
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

/** @deprecated use migratePersistedAuth */
export function sanitizePersistedAuth(persisted: unknown): Record<string, unknown> {
  return migratePersistedAuth(persisted);
}

export { AUTH_STORAGE_KEY, AUTH_PERSIST_VERSION };

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      status: "unauthenticated",
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

      setHydrated: (value) => set({ isHydrated: value }),

      clearError: () => set({ error: null }),

      clearTransientFlags: () =>
        set({
          isInitializingSession: false,
          isSubmittingLogin: false,
          isRefreshingSession: false,
          error: null,
        }),

      login: async (email, password, remember = false) => {
        if (get().isSubmittingLogin) {
          console.debug("[authStore.login] blocked — already submitting");
          throw new ApiError("Login already in progress", 429, {
            code: "LOGIN_IN_PROGRESS",
          });
        }
        console.debug("[authStore.login] start → POST /api/v1/auth/login");
        set({
          isSubmittingLogin: true,
          error: null,
        });
        try {
          const raw = await loginRequest(email, password);
          const session = parseLoginResponse(raw);
          console.debug("[authStore.login] parsed session");
          set({
            accessToken: session.accessToken,
            refreshToken: session.refreshToken,
            user: session.user,
            role: session.role,
            tokenExpiresAt: tokenExpiry(session.accessToken),
            activeOrganizationId: session.user.organization_id ?? null,
          });
          const redirect = await get().resolveAfterLogin(remember);
          console.debug("[authStore.login] done", { redirect });
          return { redirect };
        } catch (error) {
          console.debug("[authStore.login] error", error);
          const message = normalizeApiError(error);
          const status: AuthStatus =
            error instanceof ApiError && error.status === 403
              ? "forbidden"
              : "unauthenticated";
          set({ status, error: message });
          throw error;
        } finally {
          set({ isSubmittingLogin: false });
        }
      },

      resolveAfterLogin: async (remember = false) => {
        const { accessToken, user, role } = get();
        if (!accessToken || !user) {
          set({ status: "unauthenticated" });
          return "/login";
        }
        const me = await fetchMe(accessToken);
        set({ memberships: me.memberships });

        if (
          me.requires_organization_selection ||
          (me.memberships.length > 1 && !me.active_organization_id)
        ) {
          set({ status: "organization_required" });
          return "/select-organization";
        }

        const orgId =
          me.active_organization_id ?? me.memberships[0]?.organization_id ?? null;
        let capabilities: AuthCapabilities;
        try {
          capabilities = await fetchCapabilities(accessToken, orgId);
        } catch {
          set({ status: "forbidden", error: "Unable to resolve permissions" });
          return "/forbidden";
        }

        set({
          capabilities,
          activeOrganizationId: orgId,
          status: "authenticated",
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
          });
          setAuthCookies(role ?? user?.role ?? "", organizationId);
          return capabilities.workspace;
        } catch (error) {
          const message = normalizeApiError(error);
          set({ status: "forbidden", error: message });
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
            // proceed with local cleanup
          }
        }
        clearAuthCookies();
        clearLegacyStorage();
        try {
          useAuthStore.persist.clearStorage();
        } catch {
          // ignore
        }
        set({
          status: "unauthenticated",
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

      restoreSession: async () => {
        const state = get();
        const { accessToken, refreshToken, user } = state;
        if (!accessToken || !user) {
          set({
            status: "unauthenticated",
            isInitializingSession: false,
            isRefreshingSession: false,
          });
          return "unauthenticated";
        }

        set({ isInitializingSession: true, error: null });
        try {
          return await withTimeout(
            (async () => {
              let token = accessToken;
              if (isTokenExpired(token)) {
                if (!refreshToken) {
                  await get().logout();
                  set({ status: "session_expired" });
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
                  set({ status: "session_expired" });
                  return "session_expired" as AuthStatus;
                } finally {
                  set({ isRefreshingSession: false });
                }
              }

              try {
                const me = await fetchMe(token);
                set({
                  memberships: me.memberships,
                  user: me.user,
                  role: me.user.role,
                });
                if (me.requires_organization_selection) {
                  set({ status: "organization_required" });
                  return "organization_required" as AuthStatus;
                }
                const orgId =
                  me.active_organization_id ??
                  me.memberships[0]?.organization_id ??
                  null;
                const capabilities = await fetchCapabilities(token, orgId);
                set({
                  capabilities,
                  activeOrganizationId: orgId,
                  status: "authenticated",
                });
                setAuthCookies(me.user.role, orgId);
                return "authenticated" as AuthStatus;
              } catch (error) {
                if (error instanceof ApiError && error.status === 401) {
                  await get().logout();
                  set({
                    status: "session_expired",
                    error: "Your session has expired. Please sign in again.",
                  });
                  return "session_expired" as AuthStatus;
                }
                if (error instanceof ApiError && error.status === 403) {
                  set({
                    status: "forbidden",
                    error: normalizeApiError(error),
                  });
                  return "forbidden" as AuthStatus;
                }
                set({
                  status: "unauthenticated",
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
            error: normalizeApiError(error),
          });
          return "unauthenticated";
        } finally {
          set({
            isInitializingSession: false,
            isRefreshingSession: false,
          });
        }
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
        const finish = (patch: Partial<AuthState>) => {
          useAuthStore.setState({
            isHydrated: true,
            isInitializingSession: false,
            isSubmittingLogin: false,
            isRefreshingSession: false,
            error: null,
            ...patch,
          });
        };

        if (error) {
          console.debug("[authStore.rehydrate] failure → anonymous", error);
          finish({ status: "unauthenticated" });
          return;
        }

        if (!state?.accessToken || !state.user) {
          console.debug("[authStore.rehydrate] anonymous");
          finish({ status: "unauthenticated" });
          return;
        }

        // Token present: leave anonymous until restoreSession validates.
        // Never leave isSubmittingLogin or a shared isLoading stuck.
        console.debug("[authStore.rehydrate] token present → await restore");
        finish({
          status: "unauthenticated",
          isInitializingSession: true,
        });
      },
    },
  ),
);
