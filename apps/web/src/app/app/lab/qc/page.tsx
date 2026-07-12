"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchQcStatus, type QcItem } from "@/lib/api/lab";

function QcPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<QcItem[]>(
    () => fetchQcStatus({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Quality control"
        description="QC status for controls and runs."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No QC items."
        onRetry={state.reload}
      >
        <SimpleTable<QcItem>
          rows={rows}
          rowKey={(row, index) => `${row.sample_code}-${index}`}
          columns={[
            { key: "sample", label: "Sample", render: (r) => r.sample_code },
            { key: "test", label: "Test", render: (r) => r.test ?? "—" },
            { key: "lot", label: "Control lot", render: (r) => r.control_lot ?? "—" },
            { key: "note", label: "Note", render: (r) => r.note ?? "—" },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function LabQcPage() {
  return (
    <WorkspaceScreen title="Quality control" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <QcPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
