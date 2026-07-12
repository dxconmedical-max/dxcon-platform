"use client";

import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { DataState, SectionHeader, StatusPill } from "@/components/workspace/primitives";
import { fetchSpecimenTimeline, type LimsTimelineEvent } from "@/lib/api/lab";
import { normalizeApiError } from "@/lib/errors";

function TimelinePanel({ accessToken, organizationId }: WorkspaceContext) {
  const [specimenId, setSpecimenId] = useState("");
  const [events, setEvents] = useState<LimsTimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  async function load(id: string) {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    setLoaded(true);
    try {
      const result = await fetchSpecimenTimeline(
        { token: accessToken, organizationId },
        id.trim(),
      );
      setEvents(result.value);
    } catch (err) {
      setEvents([]);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="Status timeline" description="Full specimen lifecycle transition history." />

      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void load(specimenId);
        }}
      >
        <Input
          value={specimenId}
          onChange={(event) => setSpecimenId(event.target.value)}
          placeholder="Specimen ID (from specimen list)"
        />
        <Button type="submit" disabled={!specimenId.trim() || loading}>
          Load
        </Button>
      </form>

      {loaded ? (
        <DataState
          loading={loading}
          error={error}
          empty={events.length === 0}
          emptyLabel="No transitions recorded for this specimen."
          onRetry={() => void load(specimenId)}
        >
          <ol className="relative space-y-4 border-l border-slate-200 pl-6">
            {events.map((event) => (
              <li key={event.id} className="relative">
                <span className="absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 border-white bg-teal-500" />
                <div className="flex flex-wrap items-center gap-2">
                  <StatusPill status={event.to_status} />
                  {event.from_status ? (
                    <span className="text-xs text-slate-400">from {event.from_status}</span>
                  ) : null}
                </div>
                <p className="text-xs text-slate-500">
                  {event.transitioned_at}
                  {event.actor ? ` · ${event.actor}` : ""}
                </p>
                {event.note ? <p className="text-sm text-slate-700">{event.note}</p> : null}
              </li>
            ))}
          </ol>
        </DataState>
      ) : (
        <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          Enter a specimen ID to view its lifecycle timeline.
        </p>
      )}
    </div>
  );
}

export default function LabTimelinePage() {
  return (
    <WorkspaceScreen title="Status timeline" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <TimelinePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
