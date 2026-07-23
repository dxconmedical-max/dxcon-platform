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

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      status: "loading",
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
        set({ status: "loading", error: null });
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
        } finally {
          // Never leave the store stuck on bootstrap/submit "loading".
          if (get().status === "loading") {
            console.debug("[authStore.login] finally → unauthenticated");
            set({ status: "unauthenticated" });
          }
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

        if (me.requires_organization_selection || me.memberships.length > 1 && !me.active_organization_id) {
          set({ status: "organization_required" });
          return "/select-organization";
        }

        const orgId = me.active_organization_id ?? me.memberships[0]?.organization_id ?? null;
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

        let token = accessToken;
        if (isTokenExpired(token)) {
          if (!refreshToken) {
            await get().logout();
            set({ status: "session_expired" });
            return "session_expired";
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
            return "session_expired";
          }
        }

        try {
          const me = await fetchMe(token);
          set({ memberships: me.memberships, user: me.user, role: me.user.role });
          if (me.requires_organization_selection) {
            set({ status: "organization_required" });
            return "organization_required";
          }
          const orgId =
            me.active_organization_id ?? me.memberships[0]?.organization_id ?? null;
          const capabilities = await fetchCapabilities(token, orgId);
          set({
            capabilities,
            activeOrganizationId: orgId,
            status: "authenticated",
          });
          setAuthCookies(me.user.role, orgId);
          return "authenticated";
        } catch (error) {
          if (error instanceof ApiError && error.status === 401) {
            await get().logout();
            set({ status: "session_expired" });
            return "session_expired";
          }
          if (error instanceof ApiError && error.status === 403) {
            set({ status: "forbidden" });
            return "forbidden";
          }
          set({ status: "unauthenticated" });
          return "unauthenticated";
        }
      },
    }),
    {
      name: "dxcon-auth-v2",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        role: state.role,
        tokenExpiresAt: state.tokenExpiresAt,
        activeOrganizationId: state.activeOrganizationId,
      }),
      onRehydrateStorage: () => (state) => {
        // status is not persisted; leave bootstrap "loading" only when a token
        // exists (session restore). Otherwise unlock the login form immediately.
        if (!state) return;
        const nextStatus = state.accessToken ? "loading" : "unauthenticated";
        console.debug("[authStore.rehydrate] setHydrated", {
          hasToken: Boolean(state.accessToken),
          nextStatus,
        });
        useAuthStore.setState({
          isHydrated: true,
          status: nextStatus,
        });
      },
    },
  ),
);
