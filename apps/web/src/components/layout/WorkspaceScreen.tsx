"use client";

import type { ReactNode } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";

export type WorkspaceContext = {
  accessToken: string;
  organizationId: string;
  userId?: string;
  userName?: string;
  role?: string;
};

/**
 * Reusable wrapper for custom (non-table) workspace screens. Handles the auth
 * shell, permission gating, and session readiness so page components can focus
 * on their content via the render prop. Mirrors the gating in PilotListPage.
 */
export function WorkspaceScreen({
  title,
  workspacePath,
  permission,
  children,
}: {
  title: string;
  workspacePath: string;
  permission?: string;
  children: (ctx: WorkspaceContext) => ReactNode;
}) {
  const { accessToken, activeOrganizationId, can, user, role } = useAuth();
  const permissionDenied = Boolean(permission && !can(permission));

  return (
    <AppShell title={title} workspacePath={workspacePath}>
      {permissionDenied ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          You do not have permission to view this workspace.
        </div>
      ) : accessToken && activeOrganizationId ? (
        children({
          accessToken,
          organizationId: activeOrganizationId,
          userId: user?.id,
          userName: user?.email,
          role: role ?? user?.role ?? undefined,
        })
      ) : (
        <p className="text-sm text-slate-500">Loading session…</p>
      )}
    </AppShell>
  );
}
