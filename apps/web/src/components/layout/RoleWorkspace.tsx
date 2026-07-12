"use client";

import { AppShell } from "@/components/layout/AppShell";
import { RoleWorkspacePanel } from "@/components/layout/RoleWorkspacePanel";
import type { WorkspaceKey } from "@/lib/workspaces";
import { workspaceByKey } from "@/lib/workspaces";

export function RoleWorkspace({ workspaceKey }: { workspaceKey: WorkspaceKey }) {
  const definition = workspaceByKey(workspaceKey);

  return (
    <AppShell title={definition.title} workspacePath={definition.path}>
      <RoleWorkspacePanel workspaceKey={workspaceKey} />
    </AppShell>
  );
}
