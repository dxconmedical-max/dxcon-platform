"use client";

import { useEffect, useState } from "react";

import { WorkspaceHome } from "@/components/layout/WorkspaceHome";
import type { StatusCard } from "@/components/layout/WorkspaceHome";
import { fetchWorkspaceDashboard } from "@/lib/api/workspaces";
import { normalizeApiError } from "@/lib/errors";
import type { WorkspaceKey } from "@/lib/workspaces";
import { workspaceByKey } from "@/lib/workspaces";
import { useAuth } from "@/hooks/useAuth";

export type DashboardState = {
  cards: StatusCard[];
  loading: boolean;
  error: string | null;
  loaded: boolean;
};

function WorkspaceDashboardPanel({
  workspaceKey,
  title,
  subtitle,
  accessToken,
  organizationId,
}: {
  workspaceKey: WorkspaceKey;
  title: string;
  subtitle: string;
  accessToken: string;
  organizationId: string;
}) {
  const definition = workspaceByKey(workspaceKey);
  const [state, setState] = useState<DashboardState>({
    cards: definition.extractStatusCards({}),
    loading: true,
    error: null,
    loaded: false,
  });

  useEffect(() => {
    let cancelled = false;

    void fetchWorkspaceDashboard(workspaceKey, accessToken, organizationId)
      .then((data) => {
        if (cancelled) return;
        setState({
          cards: definition.extractStatusCards(data),
          loading: false,
          error: null,
          loaded: true,
        });
      })
      .catch((fetchError) => {
        if (cancelled) return;
        setState({
          cards: definition.extractStatusCards({}),
          loading: false,
          error: normalizeApiError(fetchError),
          loaded: false,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [workspaceKey, accessToken, organizationId, definition]);

  return (
    <WorkspaceHome
      title={title}
      subtitle={subtitle}
      statusCards={state.cards}
      actions={definition.actions}
      loading={state.loading}
      error={state.error}
      dataLoaded={state.loaded}
    />
  );
}

export function RoleWorkspacePanel({ workspaceKey }: { workspaceKey: WorkspaceKey }) {
  const definition = workspaceByKey(workspaceKey);
  const { accessToken, activeOrganizationId, isAuthenticated } = useAuth();

  if (!isAuthenticated || !accessToken || !activeOrganizationId) {
    return (
      <WorkspaceHome
        title={definition.title}
        subtitle={definition.subtitle}
        statusCards={definition.extractStatusCards({})}
        actions={definition.actions}
      />
    );
  }

  return (
    <WorkspaceDashboardPanel
      key={`${workspaceKey}:${accessToken}:${activeOrganizationId}`}
      workspaceKey={workspaceKey}
      title={definition.title}
      subtitle={definition.subtitle}
      accessToken={accessToken}
      organizationId={activeOrganizationId}
    />
  );
}
