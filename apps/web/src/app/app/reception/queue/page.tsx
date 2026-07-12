"use client";

import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { checkInPatient, fetchReceptionQueue, type QueueEntry } from "@/lib/api/reception";

function QueuePanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<QueueEntry[]>(
    () => fetchReceptionQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const rows = (state.data ?? []).map((entry) =>
    overrides[entry.id]
      ? { ...entry, status: overrides[entry.id], checked_in: overrides[entry.id] === "CHECKED_IN" }
      : entry,
  );

  async function checkIn(id: string) {
    setBusy(id);
    try {
      const result = await checkInPatient({ token: accessToken, organizationId }, id);
      setOverrides((prev) => ({ ...prev, [id]: result.value.status }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Today's queue"
        description="Patients waiting for check-in and service."
        source={state.source ?? undefined}
        actions={
          <Button size="sm" variant="outline" onClick={state.reload}>
            Refresh
          </Button>
        }
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="Queue is empty."
        onRetry={state.reload}
      >
        <SimpleTable<QueueEntry>
          rows={rows}
          rowKey={(row) => row.id}
          columns={[
            { key: "arrived", label: "Arrived", render: (r) => r.arrived_at ?? "—" },
            { key: "patient", label: "Patient", render: (r) => r.patient_name },
            { key: "code", label: "Code", render: (r) => r.patient_code ?? "—" },
            { key: "service", label: "Service", render: (r) => r.service ?? "—" },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
            {
              key: "action",
              label: "",
              render: (r) =>
                r.checked_in ? (
                  <span className="text-xs text-emerald-700">Checked in</span>
                ) : (
                  <Button size="sm" disabled={busy === r.id} onClick={() => checkIn(r.id)}>
                    {busy === r.id ? "…" : "Check in"}
                  </Button>
                ),
            },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function ReceptionQueuePage() {
  return (
    <WorkspaceScreen title="Queue" workspacePath="/app/reception" permission="reception.read">
      {(ctx) => <QueuePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
