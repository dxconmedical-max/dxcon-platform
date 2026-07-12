"use client";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader, StatusPill } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import {
  fetchIoTAlerts,
  fetchIoTExcursions,
  fetchIoTTrips,
  fetchLogisticsDashboard,
} from "@/lib/api/iot";

export default function OperationsLogisticsPage() {
  return (
    <WorkspaceScreen title="Live logistics" workspacePath="/app/operations/logistics" permission="executive.read">
      {({ accessToken, organizationId }) => (
        <OperationsLogisticsPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function OperationsLogisticsPanel({
  accessToken,
  organizationId,
}: {
  accessToken: string;
  organizationId: string;
}) {
  const ctx = { token: accessToken, organizationId };
  const dash = useSourcedData(() => fetchLogisticsDashboard(ctx), [accessToken, organizationId]);
  const trips = useSourcedData(() => fetchIoTTrips(ctx), [accessToken, organizationId]);
  const alerts = useSourcedData(() => fetchIoTAlerts(ctx), [accessToken, organizationId]);
  const excursions = useSourcedData(() => fetchIoTExcursions(ctx), [accessToken, organizationId]);

  const kpis = dash.data?.kpis;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Operations — live trip board"
        description="Active trips, device health, excursions, and alert queue."
        source={dash.source ?? undefined}
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {[
          ["Active trips", kpis?.active_trips],
          ["Open alerts", kpis?.open_alerts],
          ["Excursions", kpis?.active_excursions],
          ["Offline devices", kpis?.offline_devices],
          ["Delayed trips", kpis?.delayed_trips],
        ].map(([label, value]) => (
          <Card key={String(label)} className="p-4">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-2xl font-semibold text-slate-900">{value ?? "—"}</p>
          </Card>
        ))}
      </div>

      <DataState
        loading={trips.loading}
        error={trips.error}
        empty={(trips.data?.trips.length ?? 0) === 0}
        emptyLabel="No active trips. Trips appear here when collectors start transport."
        onRetry={trips.reload}
      >
        <Card className="p-4">
          <h3 className="mb-3 font-medium text-slate-900">Live trips</h3>
          <ul className="space-y-2">
            {(trips.data?.trips ?? []).map((trip) => (
              <li key={trip.id} className="flex items-center justify-between text-sm">
                <span>{trip.trip_code}</span>
                <StatusPill status={trip.status} />
              </li>
            ))}
          </ul>
        </Card>
      </DataState>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-4">
          <h3 className="mb-3 font-medium text-slate-900">Alert queue</h3>
          <DataState
            loading={alerts.loading}
            error={alerts.error}
            empty={(alerts.data?.alerts.length ?? 0) === 0}
            emptyLabel="No open alerts."
            onRetry={alerts.reload}
          >
            <ul className="space-y-2 text-sm">
              {(alerts.data?.alerts ?? []).slice(0, 10).map((a) => (
                <li key={a.id} className="flex justify-between gap-2">
                  <span className="truncate">{a.message ?? a.alert_type}</span>
                  <StatusPill status={a.severity} />
                </li>
              ))}
            </ul>
          </DataState>
        </Card>

        <Card className="p-4">
          <h3 className="mb-3 font-medium text-slate-900">Active excursions</h3>
          <DataState
            loading={excursions.loading}
            error={excursions.error}
            empty={(excursions.data?.excursions.length ?? 0) === 0}
            emptyLabel="No cold-chain excursions detected."
            onRetry={excursions.reload}
          >
            <ul className="space-y-2 text-sm">
              {(excursions.data?.excursions ?? []).map((e) => (
                <li key={e.id} className="flex justify-between">
                  <span>{e.excursion_type}</span>
                  <StatusPill status={e.state} />
                </li>
              ))}
            </ul>
          </DataState>
        </Card>
      </div>
    </div>
  );
}
