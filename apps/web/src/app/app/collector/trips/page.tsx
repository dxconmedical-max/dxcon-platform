"use client";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader, StatusPill } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchIoTTrips } from "@/lib/api/iot";

export default function CollectorTripsPage() {
  return (
    <WorkspaceScreen title="Assigned trips" workspacePath="/app/collector/trips" permission="collections.read">
      {({ accessToken, organizationId }) => (
        <CollectorTripsPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function CollectorTripsPanel({
  accessToken,
  organizationId,
}: {
  accessToken: string;
  organizationId: string;
}) {
  const state = useSourcedData(
    () => fetchIoTTrips({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const trips = state.data?.trips ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Assigned trips"
        description="Your transport assignments, check-in, and handover."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={trips.length === 0}
        emptyLabel="No trips assigned. New assignments appear when dispatch schedules your route."
        onRetry={state.reload}
      >
        <div className="space-y-3">
          {trips.map((trip) => (
            <Card key={trip.id} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">{trip.trip_code}</p>
                  {trip.vehicle_id ? (
                    <p className="text-xs text-slate-500">Vehicle {trip.vehicle_id}</p>
                  ) : null}
                </div>
                <StatusPill status={trip.status} />
              </div>
            </Card>
          ))}
        </div>
      </DataState>
    </div>
  );
}
