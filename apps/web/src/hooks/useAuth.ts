"use client";

import { useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";

import { can, canAny, canAll, hasFeature, isOrganizationType, isWorkspace } from "@/lib/permissions";
import { isWorkspacePath, workspacePathForRole } from "@/lib/roles";
import { useAuthStore } from "@/stores/authStore";

export function useAuth() {
  const store = useAuthStore();
  return {
    ...store,
    isAuthenticated: store.status === "authenticated",
    isInitializingSession: store.isInitializingSession || !store.isHydrated,
    isSubmittingLogin: store.isSubmittingLogin,
    isRefreshingSession: store.isRefreshingSession,
    capabilities: store.capabilities,
    can: (permission: string) => can(store.capabilities, permission),
    canAny: (permissions: string[]) => canAny(store.capabilities, permissions),
    canAll: (permissions: string[]) => canAll(store.capabilities, permissions),
    hasFeature: (feature: string) => hasFeature(store.capabilities, feature),
    isWorkspace: (workspace: string) => isWorkspace(store.capabilities, workspace),
    isOrganizationType: (type: string) =>
      isOrganizationType(store.capabilities, type),
    workspacePath:
      store.capabilities?.workspace ??
      workspacePathForRole(store.role ?? store.user?.role),
  };
}

const ADMIN_ROLES = new Set([
  "SUPER_ADMIN",
  "DXCON_ADMIN",
  "ADMIN",
  "SYSTEM_ADMIN",
]);

/**
 * Protect workspace routes. Must NOT depend on a freshly-allocated `auth`
 * object — that re-ran restoreSession on every store tick and left
 * /app/admin spinning forever after login.
 */
export function useRequireAuth(workspacePath?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const isHydrated = useAuthStore((s) => s.isHydrated);
  const status = useAuthStore((s) => s.status);
  const isInitializingSession = useAuthStore((s) => s.isInitializingSession);
  const error = useAuthStore((s) => s.error);
  const restoreSession = useAuthStore((s) => s.restoreSession);
  const bootstrapGeneration = useRef(0);

  useEffect(() => {
    if (!isHydrated) return;

    const generation = ++bootstrapGeneration.current;
    let cancelled = false;

    const guard = async () => {
      const state = useAuthStore.getState();

      // Post-login navigation already resolved me + capabilities.
      // Do not flip isInitializingSession again or the shell flashes/spins.
      if (
        state.status === "authenticated" &&
        state.capabilities &&
        state.accessToken
      ) {
        enforceWorkspace(workspacePath, router);
        return;
      }

      const next = await restoreSession();
      if (cancelled || generation !== bootstrapGeneration.current) return;

      if (next === "unauthenticated" || next === "session_expired") {
        router.replace(
          next === "session_expired"
            ? "/login?reason=session-expired"
            : "/login",
        );
        return;
      }
      if (next === "organization_required") {
        router.replace("/select-organization");
        return;
      }
      if (next === "forbidden") {
        router.replace("/forbidden");
        return;
      }

      enforceWorkspace(workspacePath, router);
    };

    void guard();
    return () => {
      cancelled = true;
    };
    // Intentionally omit unstable auth object — use stable store selectors only.
  }, [isHydrated, workspacePath, pathname, restoreSession, router]);

  const auth = useAuth();
  return {
    ...auth,
    // Prefer live selector values for shell gates (avoid stale spread).
    isHydrated,
    status,
    isInitializingSession: isInitializingSession || !isHydrated,
    error,
    isAuthenticated: status === "authenticated",
  };
}

function enforceWorkspace(
  workspacePath: string | undefined,
  router: ReturnType<typeof useRouter>,
) {
  if (!workspacePath) return;
  const state = useAuthStore.getState();
  const capabilities = state.capabilities;
  if (!capabilities) return;

  const home = capabilities.workspace;
  const role = (state.role ?? "").toUpperCase();
  const isAdmin = ADMIN_ROLES.has(role);
  if (
    !isAdmin &&
    workspacePath !== home &&
    workspacePath !== "/app" &&
    isWorkspacePath(workspacePath)
  ) {
    router.replace(home || "/app");
  }
}
