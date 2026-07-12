import { apiRequest } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";
import {
  SAMPLE_COLLECTION_JOBS,
  SAMPLE_ROUTE_STOPS,
  SAMPLE_TIMELINE,
} from "./samples";

export type CollectionJob = {
  assignment_id: string;
  patient_name: string;
  address?: string;
  scheduled_at?: string;
  service?: string;
  status: string;
  priority?: string;
};

export type RouteStop = {
  sequence: number;
  label: string;
  eta?: string;
  status: string;
};

export type TimelineEvent = {
  at: string;
  event: string;
  actor?: string;
  location?: string;
};

type Ctx = { token: string; organizationId: string; collectorId?: string };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

function mapJobs(rows: Record<string, unknown>[]): CollectionJob[] {
  return rows.map((row) => ({
    assignment_id: String(row.assignment_id ?? row.id ?? "—"),
    patient_name: String(row.patient_name ?? row.full_name ?? row.name ?? "—"),
    address: row.address ? String(row.address) : undefined,
    scheduled_at: row.scheduled_at ? String(row.scheduled_at) : undefined,
    service: String(row.service ?? row.test ?? row.description ?? "—"),
    status: String(row.status ?? "ASSIGNED").toUpperCase(),
    priority: row.priority ? String(row.priority) : undefined,
  }));
}

/** Assigned collection jobs. Backed by collector-operations jobs when a
 * collector id is available; labeled sample fallback otherwise. */
export async function fetchCollectionJobs({
  token,
  organizationId,
  collectorId,
}: Ctx): Promise<Sourced<CollectionJob[]>> {
  if (!collectorId) {
    return { value: SAMPLE_COLLECTION_JOBS, source: "sample", note: SAMPLE_NOTE };
  }
  return withSampleFallback<CollectionJob[]>(
    async () => {
      const response = await apiRequest<{ jobs?: unknown; data?: unknown }>(
        `/api/v1/collector-operations/collectors/${encodeURIComponent(collectorId)}/jobs`,
        { token, organizationId },
      );
      const raw = asArray(
        (response as { jobs?: unknown }).jobs ?? (response as { data?: unknown }).data,
      );
      const jobs = mapJobs(raw);
      if (jobs.length === 0) throw new Error("no jobs");
      return jobs;
    },
    SAMPLE_COLLECTION_JOBS,
    SAMPLE_NOTE,
  );
}

/** Today's route stops. Labeled sample adapter (requires route context). */
export async function fetchRouteStops({
  token,
  organizationId,
  collectorId,
}: Ctx): Promise<Sourced<RouteStop[]>> {
  if (!collectorId) {
    return { value: SAMPLE_ROUTE_STOPS, source: "sample", note: SAMPLE_NOTE };
  }
  return withSampleFallback<RouteStop[]>(
    async () => {
      const response = await apiRequest<{ routes?: unknown; data?: unknown }>(
        `/api/v1/collector-operations/collectors/${encodeURIComponent(collectorId)}/routes`,
        { token, organizationId },
      );
      const routes = asArray(
        (response as { routes?: unknown }).routes ?? (response as { data?: unknown }).data,
      );
      const first = routes[0] as Record<string, unknown> | undefined;
      const stops = asArray(first?.stops).map((row, index) => ({
        sequence: Number(row.sequence ?? index + 1),
        label: String(row.label ?? row.address ?? row.patient_name ?? "—"),
        eta: row.eta ? String(row.eta) : undefined,
        status: String(row.status ?? "PENDING").toUpperCase(),
      }));
      if (stops.length === 0) throw new Error("no stops");
      return stops;
    },
    SAMPLE_ROUTE_STOPS,
    SAMPLE_NOTE,
  );
}

/** Collection timeline. Backed by collector-operations timeline; sample fallback. */
export async function fetchCollectionTimeline({
  token,
  organizationId,
  collectorId,
}: Ctx): Promise<Sourced<TimelineEvent[]>> {
  if (!collectorId) {
    return { value: SAMPLE_TIMELINE, source: "sample", note: SAMPLE_NOTE };
  }
  return withSampleFallback<TimelineEvent[]>(
    async () => {
      const response = await apiRequest<{ timeline?: unknown; data?: unknown }>(
        `/api/v1/collector-operations/collectors/${encodeURIComponent(collectorId)}/timeline?limit=25`,
        { token, organizationId },
      );
      const raw = asArray(
        (response as { timeline?: unknown }).timeline ?? (response as { data?: unknown }).data,
      );
      const events = raw.map((row) => ({
        at: String(row.at ?? row.timestamp ?? row.created_at ?? "—"),
        event: String(row.event ?? row.description ?? row.type ?? "—"),
        actor: row.actor ? String(row.actor) : undefined,
        location: row.location ? String(row.location) : undefined,
      }));
      if (events.length === 0) throw new Error("no timeline");
      return events;
    },
    SAMPLE_TIMELINE,
    SAMPLE_NOTE,
  );
}

/**
 * Upload a specimen proof photo (base64). Backed by
 * POST /api/v1/collector-operations/proofs; sample echo on failure.
 */
export async function uploadSpecimenPhoto(
  { token, organizationId }: Ctx,
  payload: { assignmentId: string; fileName: string; contentBase64: string },
): Promise<Sourced<{ proof_id: string; message: string }>> {
  return withSampleFallback<{ proof_id: string; message: string }>(
    async () => {
      const response = await apiRequest<{ proof_id?: string; id?: string; data?: Record<string, unknown> }>(
        "/api/v1/collector-operations/proofs",
        {
          token,
          organizationId,
          method: "POST",
          body: {
            proof_type: "SPECIMEN_PHOTO",
            reference: payload.assignmentId,
            file_name: payload.fileName,
            content_base64: payload.contentBase64,
          },
        },
      );
      const id = response.proof_id ?? response.id ?? (response.data?.id as string | undefined);
      if (!id) throw new Error("no proof id");
      return { proof_id: String(id), message: "Specimen photo uploaded." };
    },
    {
      proof_id: `PROOF-${Math.floor(1000 + Math.random() * 8999)}`,
      message: "Specimen photo captured locally (no live backend response).",
    },
    SAMPLE_NOTE,
  );
}
