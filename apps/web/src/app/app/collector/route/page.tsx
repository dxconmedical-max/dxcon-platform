"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import {
  DataState,
  MapPlaceholder,
  SectionHeader,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchRouteStops, type RouteStop } from "@/lib/api/collector";

function RoutePanel({ accessToken, organizationId, userId }: WorkspaceContext) {
  const state = useSourcedData<RouteStop[]>(
    () => fetchRouteStops({ token: accessToken, organizationId, collectorId: userId }),
    [accessToken, organizationId, userId],
  );
  const stops = state.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Today's route"
        description="Optimized stops for your collection route."
        source={state.source ?? undefined}
      />

      <MapPlaceholder
        stops={stops.length}
        onNavigate={() => {
          const first = stops.find((s) => s.status !== "DONE");
          if (first) {
            window.open(
              `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(first.label)}`,
              "_blank",
              "noopener",
            );
          }
        }}
      />

      <DataState
        loading={state.loading}
        error={state.error}
        empty={stops.length === 0}
        emptyLabel="No stops planned for today."
        onRetry={state.reload}
      >
        <div className="space-y-3">
          {stops.map((stop) => (
            <Card key={stop.sequence} className="flex items-center gap-4">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-teal-50 text-sm font-semibold text-teal-700">
                {stop.sequence}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-slate-900">{stop.label}</p>
                {stop.eta ? <p className="text-xs text-slate-500">ETA {stop.eta}</p> : null}
              </div>
              <StatusPill status={stop.status} />
            </Card>
          ))}
        </div>
      </DataState>
    </div>
  );
}

export default function CollectorRoutePage() {
  return (
    <WorkspaceScreen title="Route" workspacePath="/app/collector" permission="collections.read">
      {(ctx) => <RoutePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
