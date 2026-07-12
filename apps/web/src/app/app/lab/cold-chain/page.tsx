"use client";

import { useState } from "react";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader, StatusPill } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchContainerReadings, fetchIoTExcursions } from "@/lib/api/iot";

export default function LabColdChainPage() {
  return (
    <WorkspaceScreen title="Cold chain" workspacePath="/app/lab/cold-chain" permission="lab.read">
      {({ accessToken, organizationId }) => (
        <LabColdChainPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function LabColdChainPanel({
  accessToken,
  organizationId,
}: {
  accessToken: string;
  organizationId: string;
}) {
  const [deviceId, setDeviceId] = useState("");
  const ctx = { token: accessToken, organizationId };
  const excursions = useSourcedData(() => fetchIoTExcursions(ctx), [accessToken, organizationId]);
  const readings = useSourcedData(
    () => (deviceId ? fetchContainerReadings(ctx, deviceId) : Promise.resolve({ value: { readings: [] }, source: "live" as const })),
    [accessToken, organizationId, deviceId],
  );

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Inbound cold chain"
        description="Container temperature history, excursions, and specimen hold status."
        source={excursions.source ?? undefined}
      />

      <Card className="p-4">
        <label className="text-sm font-medium text-slate-700">Device / container ID</label>
        <input
          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          placeholder="Enter device ID to load temperature history"
          value={deviceId}
          onChange={(e) => setDeviceId(e.target.value)}
        />
      </Card>

      <DataState
        loading={excursions.loading}
        error={excursions.error}
        empty={(excursions.data?.excursions.length ?? 0) === 0}
        emptyLabel="No excursions on record. Excursions require configured threshold policies and live telemetry."
        onRetry={excursions.reload}
      >
        <Card className="p-4">
          <h3 className="mb-3 font-medium">Excursion status</h3>
          <ul className="space-y-2 text-sm">
            {(excursions.data?.excursions ?? []).map((e) => (
              <li key={e.id} className="flex justify-between">
                <span>
                  {e.excursion_type}
                  {e.specimen_hold ? " — specimen on hold" : ""}
                </span>
                <StatusPill status={e.state} />
              </li>
            ))}
          </ul>
        </Card>
      </DataState>

      {deviceId ? (
        <Card className="p-4">
          <h3 className="mb-3 font-medium">Temperature history</h3>
          <DataState
            loading={readings.loading}
            error={readings.error}
            empty={(readings.data?.readings.length ?? 0) === 0}
            emptyLabel="No readings for this device yet."
            onRetry={readings.reload}
          >
            <ul className="max-h-64 space-y-1 overflow-y-auto text-xs text-slate-600">
              {(readings.data?.readings ?? []).map((r) => (
                <li key={r.id}>
                  {r.recorded_at}: {r.temperature_c ?? "—"}°C
                  {r.simulated ? " (SIMULATED)" : ""}
                </li>
              ))}
            </ul>
          </DataState>
        </Card>
      ) : null}
    </div>
  );
}
