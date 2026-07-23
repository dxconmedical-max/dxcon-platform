"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

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
  | "loading"
  | "unauthenticated"
  | "authenticated"
  | "session_expired"
  | "forbidden"
  | "organization_required"
  | "workspace_required";

const SESSION_RESTORE_TIMEOUT_MS = 15_000;
export const AUTH_STORAGE_KEY = "dxcon-auth-v2";

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

  setHydrated: (value: boolean) => void;
  clearError: () => void;
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

/** Drop transient fields if an older build ever persisted them. */
export function sanitizePersistedAuth(persisted: unknown): Record<string, unknown> {
  if (!persisted || typeof persisted !== "object") return {};
  const state = { ...(persisted as Record<string, unknown>) };
  delete state.status;
  delete state.error;
  delete state.isHydrated;
  delete state.isLoading;
  delete state.isSubmittingLogin;
  delete state.memberships;
  delete state.capabilities;
  return state;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Never start as "loading" — that previously drove the login button.
      // Session restore sets "loading" only while a token is being validated.
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

      setHydrated: (value) => set({ isHydrated: value }),

      clearError: () => set({ error: null }),

      login: async (email, password, remember = false) => {
        console.debug("[authStore.login] start");
        // Do not set status:"loading" here — that is session init, not submit.
        set({ error: null });
        try {
          console.debug("[authStore.login] calling loginRequest → POST /api/v1/auth/login");
          const response = await loginRequest(email, password);
          console.debug("[authStore.login] loginRequest resolved");
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            user: response.user,
            role: response.role,
            tokenExpiresAt: tokenExpiry(response.access_token),
            activeOrganizationId: response.user.organization_id ?? null,
          });
          console.debug("[authStore.login] resolveAfterLogin");
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
        set({ status: "loading" });
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
          if (get().status === "loading") {
            set({ status: "unauthenticated" });
          }
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
        });
      },

      restoreSession: async () => {
        const state = get();
        const { accessToken, refreshToken, user } = state;
        if (!accessToken || !user) {
          set({ status: "unauthenticated" });
          return "unauthenticated";
        }

        set({ status: "loading" });
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
                try {
                  const refreshed = await refreshAccessToken(refreshToken);
                  token = refreshed.access_token;
                  set({
                    accessToken: token,
                    tokenExpiresAt: tokenExpiry(token),
                  });
                } catch {
                  await get().logout();
                  set({ status: "session_expired" });
                  return "session_expired" as AuthStatus;
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
                  set({ status: "session_expired" });
                  return "session_expired" as AuthStatus;
                }
                if (error instanceof ApiError && error.status === 403) {
                  set({ status: "forbidden" });
                  return "forbidden" as AuthStatus;
                }
                set({ status: "unauthenticated" });
                return "unauthenticated" as AuthStatus;
              }
            })(),
            SESSION_RESTORE_TIMEOUT_MS,
            "Session restore",
          );
        } catch (error) {
          console.debug("[authStore.restoreSession] failed/timeout", error);
          set({ status: "unauthenticated" });
          return "unauthenticated";
        } finally {
          if (get().status === "loading") {
            set({ status: "unauthenticated" });
          }
        }
      },
    }),
    {
      name: AUTH_STORAGE_KEY,
      version: 2,
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        role: state.role,
        tokenExpiresAt: state.tokenExpiresAt,
        activeOrganizationId: state.activeOrganizationId,
      }),
      migrate: (persisted) => sanitizePersistedAuth(persisted),
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.debug("[authStore.rehydrate] error → unauthenticated", error);
          useAuthStore.setState({
            isHydrated: true,
            status: "unauthenticated",
          });
          return;
        }
        // status is not persisted; never leave bootstrap "loading" active.
        // Only keep "loading" briefly when a token exists (session restore).
        if (!state) {
          useAuthStore.setState({
            isHydrated: true,
            status: "unauthenticated",
          });
          return;
        }
        const nextStatus = state.accessToken ? "loading" : "unauthenticated";
        console.debug("[authStore.rehydrate] setHydrated", {
          hasToken: Boolean(state.accessToken),
          nextStatus,
        });
        useAuthStore.setState({
          isHydrated: true,
          status: nextStatus,
          error: null,
        });
      },
    },
  ),
);
