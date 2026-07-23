"use client";

import { useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";

import { can, canAny, canAll, hasFeature, isOrganizationType, isWorkspace } from "@/lib/permissions";
import { isWorkspacePath, workspacePathForRole } from "@/lib/roles";
import { useAuthStore } from "@/stores/authStore";

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

  const restoring =
    !isHydrated ||
    bootstrapPhase === "idle" ||
    bootstrapPhase === "restoring" ||
    isInitializingSession;

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
    isInitializingSession: restoring,
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
 */
export function useRequireAuth(workspacePath?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const routerRef = useRef(router);
  routerRef.current = router;

  const isHydrated = useAuthStore((s) => s.isHydrated);
  const bootstrapPhase = useAuthStore((s) => s.bootstrapPhase);
  const status = useAuthStore((s) => s.status);
  const error = useAuthStore((s) => s.error);
  const role = useAuthStore((s) => s.role);
  const capabilities = useAuthStore((s) => s.capabilities);

  useEffect(() => {
    if (!isHydrated) return;
    // Wait until the single AuthProvider restore finishes.
    if (bootstrapPhase === "idle" || bootstrapPhase === "restoring") return;

    if (status === "unauthenticated" || status === "session_expired") {
      const target =
        status === "session_expired"
          ? "/login?reason=session-expired"
          : "/login";
      // Avoid replace loops when already on /login.
      if (!pathname.startsWith("/login")) {
        safeReplace(routerRef.current, pathname, target);
      }
      return;
    }

    if (status === "organization_required") {
      safeReplace(routerRef.current, pathname, "/select-organization");
      return;
    }

    if (status === "forbidden") {
      safeReplace(routerRef.current, pathname, "/forbidden");
      return;
    }

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
    // No router / restoreSession in deps — prevents update-depth loops.
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
