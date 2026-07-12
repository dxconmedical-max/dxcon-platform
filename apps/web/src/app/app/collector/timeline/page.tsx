"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchCollectionTimeline, type TimelineEvent } from "@/lib/api/collector";

function TimelinePanel({ accessToken, organizationId, userId }: WorkspaceContext) {
  const state = useSourcedData<TimelineEvent[]>(
    () => fetchCollectionTimeline({ token: accessToken, organizationId, collectorId: userId }),
    [accessToken, organizationId, userId],
  );
  const events = state.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Collection timeline"
        description="Recent collection and handover activity."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={events.length === 0}
        emptyLabel="No recent activity."
        onRetry={state.reload}
      >
        <ol className="relative space-y-4 border-l border-slate-200 pl-6">
          {events.map((event, index) => (
            <li key={`${event.at}-${index}`} className="relative">
              <span className="absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 border-white bg-teal-500" />
              <p className="text-sm font-medium text-slate-900">{event.event}</p>
              <p className="text-xs text-slate-500">
                {event.at}
                {event.actor ? ` · ${event.actor}` : ""}
                {event.location ? ` · ${event.location}` : ""}
              </p>
            </li>
          ))}
        </ol>
      </DataState>
    </div>
  );
}

export default function CollectorTimelinePage() {
  return (
    <WorkspaceScreen title="Timeline" workspacePath="/app/collector" permission="collections.read">
      {(ctx) => <TimelinePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
