"use client";

import { useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";

import { can, canAny, canAll, hasFeature, isOrganizationType, isWorkspace } from "@/lib/permissions";
import { isWorkspacePath, workspacePathForRole } from "@/lib/roles";
import {
  isBootstrapPending,
  useAuthStore,
} from "@/stores/authStore";

/**
 * Prefer field selectors — never subscribe to the entire store object
 * (that allocates a new snapshot every tick and invites effect loops).
 */
export function useAuth() {
  const status = useAuthStore((s) => s.status);
  const bootstrapPhase = useAuthStore((s) => s.bootstrapPhase);
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);
  const accessToken = useAuthStore((s) => s.accessToken);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const memberships = useAuthStore((s) => s.memberships);
  const activeOrganizationId = useAuthStore((s) => s.activeOrganizationId);
  const capabilities = useAuthStore((s) => s.capabilities);
  const error = useAuthStore((s) => s.error);
  const isHydrated = useAuthStore((s) => s.isHydrated);
  const isInitializingSession = useAuthStore((s) => s.isInitializingSession);
  const isSubmittingLogin = useAuthStore((s) => s.isSubmittingLogin);
  const isRefreshingSession = useAuthStore((s) => s.isRefreshingSession);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);
  const restoreSession = useAuthStore((s) => s.restoreSession);
  const selectOrganization = useAuthStore((s) => s.selectOrganization);
  const clearError = useAuthStore((s) => s.clearError);
  const clearTransientFlags = useAuthStore((s) => s.clearTransientFlags);
  const setHydrated = useAuthStore((s) => s.setHydrated);

  const isBootstrapping = !isHydrated || isBootstrapPending(bootstrapPhase);

  return {
    status,
    bootstrapPhase,
    user,
    role,
    accessToken,
    refreshToken,
    memberships,
    activeOrganizationId,
    capabilities,
    error,
    isHydrated,
    isBootstrapping,
    isInitializingSession,
    isSubmittingLogin,
    isRefreshingSession,
    isAuthenticated: status === "authenticated",
    login,
    logout,
    restoreSession,
    selectOrganization,
    clearError,
    clearTransientFlags,
    setHydrated,
    can: (permission: string) => can(capabilities, permission),
    canAny: (permissions: string[]) => canAny(capabilities, permissions),
    canAll: (permissions: string[]) => canAll(capabilities, permissions),
    hasFeature: (feature: string) => hasFeature(capabilities, feature),
    isWorkspace: (workspace: string) => isWorkspace(capabilities, workspace),
    isOrganizationType: (type: string) =>
      isOrganizationType(capabilities, type),
    workspacePath:
      capabilities?.workspace ?? workspacePathForRole(role ?? user?.role),
  };
}

const ADMIN_ROLES = new Set([
  "SUPER_ADMIN",
  "DXCON_ADMIN",
  "ADMIN",
  "SYSTEM_ADMIN",
]);

function safeReplace(
  router: { replace: (href: string) => void },
  pathname: string,
  target: string,
) {
  if (!target || target === pathname) return;
  router.replace(target);
}

/**
 * Route guard only — does NOT own restoreSession.
 * AuthProvider is the sole bootstrap owner.
 *
 * CRITICAL: never redirect while bootstrap is idle/restoring.
 * Redirect only after terminal phase === "anonymous" (or session_expired).
 */
export function useRequireAuth(workspacePath?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const routerRef = useRef(router);
  routerRef.current = router;

  const isHydrated = useAuthStore((s) => s.isHydrated);
  const bootstrapPhase = useAuthStore((s) => s.bootstrapPhase);
  const status = useAuthStore((s) => s.status);
  const role = useAuthStore((s) => s.role);
  const capabilities = useAuthStore((s) => s.capabilities);

  useEffect(() => {
    if (!isHydrated) return;
    // Must wait for restoreSession to finish — do NOT treat default
    // status:"unauthenticated" as anonymous while phase is still pending.
    if (isBootstrapPending(bootstrapPhase)) return;

    // Premature redirect: bootstrapPhase can still be "anonymous" from the
    // /login hydrate while resolveAfterLogin has already set status to
    // "authenticated" (cookies exist). Never treat that as anonymous.
    if (status === "session_expired") {
      if (!pathname.startsWith("/login")) {
        safeReplace(
          routerRef.current,
          pathname,
          "/login?reason=session-expired",
        );
      }
      return;
    }

    if (bootstrapPhase === "anonymous" && status !== "authenticated") {
      if (!pathname.startsWith("/login")) {
        safeReplace(routerRef.current, pathname, "/login");
      }
      return;
    }

    if (status === "organization_required") {
      safeReplace(routerRef.current, pathname, "/select-organization");
      return;
    }

    if (status === "forbidden" || bootstrapPhase === "failed") {
      if (status === "forbidden") {
        safeReplace(routerRef.current, pathname, "/forbidden");
      }
      return;
    }

    if (bootstrapPhase !== "authenticated") return;
    if (!workspacePath || !capabilities) return;
    const home = capabilities.workspace;
    const roleCode = (role ?? "").toUpperCase();
    const isAdmin = ADMIN_ROLES.has(roleCode);
    if (
      !isAdmin &&
      workspacePath !== home &&
      workspacePath !== "/app" &&
      isWorkspacePath(workspacePath)
    ) {
      safeReplace(routerRef.current, pathname, home || "/app");
    }
  }, [
    isHydrated,
    bootstrapPhase,
    status,
    pathname,
    workspacePath,
    capabilities,
    role,
  ]);

  return useAuth();
}
