"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

import { can, canAny, canAll, hasFeature, isOrganizationType, isWorkspace } from "@/lib/permissions";
import { isWorkspacePath, workspacePathForRole } from "@/lib/roles";
import { useAuthStore } from "@/stores/authStore";

export function useAuth() {
  const store = useAuthStore();
  return {
    ...store,
    isAuthenticated: store.status === "authenticated",
    isLoading: store.status === "loading",
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

export function useRequireAuth(workspacePath?: string) {
  const router = useRouter();
  const pathname = usePathname();
  const auth = useAuth();

  useEffect(() => {
    if (!auth.isHydrated) return;

    const guard = async () => {
      const status = await auth.restoreSession();
      if (status === "unauthenticated" || status === "session_expired") {
        router.replace(
          status === "session_expired"
            ? "/login?reason=session-expired"
            : "/login",
        );
        return;
      }
      if (status === "organization_required") {
        router.replace("/select-organization");
        return;
      }
      if (status === "forbidden") {
        router.replace("/forbidden");
        return;
      }

      if (workspacePath && auth.capabilities) {
        const home = auth.capabilities.workspace;
        const adminRoles = new Set([
          "SUPER_ADMIN",
          "DXCON_ADMIN",
          "ADMIN",
          "SYSTEM_ADMIN",
        ]);
        const role = (auth.role ?? "").toUpperCase();
        const isAdmin = adminRoles.has(role);
        if (
          !isAdmin &&
          workspacePath !== home &&
          workspacePath !== "/app" &&
          isWorkspacePath(workspacePath)
        ) {
          router.replace(home || "/app");
        }
      }
    };

    void guard();
  }, [auth.isHydrated, workspacePath, pathname, auth, router]);

  return auth;
}
