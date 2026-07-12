"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchAnalyzerQueue, type LabSample } from "@/lib/api/lab";

function QueuePanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<LabSample[]>(
    () => fetchAnalyzerQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Analyzer queue"
        description="Samples currently in testing."
        source={state.source ?? undefined}
        actions={undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No samples in the analyzer queue."
        onRetry={state.reload}
      >
        <SimpleTable<LabSample>
          rows={rows}
          rowKey={(row) => row.sample_code}
          columns={[
            { key: "sample", label: "Sample", render: (r) => r.sample_code },
            { key: "order", label: "Order", render: (r) => r.order_code ?? "—" },
            { key: "test", label: "Test", render: (r) => r.test ?? "—" },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function LabQueuePage() {
  return (
    <WorkspaceScreen title="Analyzer queue" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <QueuePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
