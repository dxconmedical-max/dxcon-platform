"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchSpecimens, type LimsSpecimen } from "@/lib/api/lab";

function SpecimensPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<{ items: LimsSpecimen[]; total: number }>(
    () => fetchSpecimens({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data?.items ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Specimens"
        description={`${state.data?.total ?? 0} specimen(s) in the LIMS registry.`}
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No specimens registered yet."
        onRetry={state.reload}
      >
        <SimpleTable<LimsSpecimen>
          rows={rows}
          rowKey={(row) => row.id}
          columns={[
            { key: "code", label: "Human ID", render: (r) => r.human_readable },
            { key: "order", label: "Order", render: (r) => r.order_code ?? "—" },
            { key: "container", label: "Container", render: (r) => r.container_type ?? "—" },
            { key: "volume", label: "Volume", render: (r) => (r.volume ? `${r.volume} ${r.volume_unit ?? "mL"}` : "—") },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function LabSpecimensPage() {
  return (
    <WorkspaceScreen title="Specimens" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <SpecimensPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
