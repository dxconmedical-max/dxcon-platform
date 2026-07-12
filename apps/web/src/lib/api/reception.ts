import { apiRequest, type ApiEnvelope } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";
import { SAMPLE_QUEUE } from "./samples";

export type QueueEntry = {
  id: string;
  patient_name: string;
  patient_code?: string;
  service?: string;
  checked_in: boolean;
  arrived_at?: string;
  status: string;
};

export type WalkInRegistration = {
  full_name: string;
  phone: string;
  date_of_birth?: string;
  gender?: string;
  note?: string;
};

type Ctx = { token: string; organizationId: string };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

function mapQueue(rows: Record<string, unknown>[]): QueueEntry[] {
  return rows.map((row) => {
    const status = String(row.status ?? "WAITING").toUpperCase();
    return {
      id: String(row.id ?? row.queue_entry_id ?? row.order_ref ?? "—"),
      patient_name: String(row.patient_name ?? row.full_name ?? row.name ?? "—"),
      patient_code: row.patient_code ? String(row.patient_code) : undefined,
      service: String(row.service ?? row.test ?? row.description ?? "—"),
      checked_in: status === "CHECKED_IN" || Boolean(row.checked_in),
      arrived_at: row.arrived_at ? String(row.arrived_at) : undefined,
      status,
    };
  });
}

/** Today's reception queue. Backed by GET /reception/workspace/queue. */
export async function fetchReceptionQueue({
  token,
  organizationId,
}: Ctx): Promise<Sourced<QueueEntry[]>> {
  return withSampleFallback<QueueEntry[]>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/reception/workspace/queue",
        { token, organizationId },
      );
      const raw = asArray(response.data?.queue ?? response.data?.workflow_queue ?? response.data);
      const queue = mapQueue(raw);
      if (queue.length === 0) throw new Error("empty queue");
      return queue;
    },
    SAMPLE_QUEUE,
    SAMPLE_NOTE,
  );
}

/** Fast patient/booking search. Backed by GET /reception/workspace/search. */
export async function searchReception(
  { token, organizationId }: Ctx,
  query: string,
): Promise<Sourced<QueueEntry[]>> {
  const sample = SAMPLE_QUEUE.filter((entry) =>
    `${entry.patient_name} ${entry.patient_code ?? ""} ${entry.service ?? ""}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return withSampleFallback<QueueEntry[]>(
    async () => {
      const params = new URLSearchParams({ q: query, limit: "25" });
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        `/api/v1/reception/workspace/search?${params}`,
        { token, organizationId },
      );
      const raw = asArray(response.data?.results ?? response.data?.patients ?? response.data);
      return mapQueue(raw);
    },
    sample,
    SAMPLE_NOTE,
  );
}

/**
 * Walk-in registration. Backed by POST /reception/workspace/patients/register.
 * Returns a patient code on success.
 */
export async function registerWalkIn(
  { token, organizationId }: Ctx,
  registration: WalkInRegistration,
): Promise<Sourced<{ patient_code: string; message: string }>> {
  return withSampleFallback<{ patient_code: string; message: string }>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/reception/workspace/patients/register",
        { token, organizationId, method: "POST", body: registration },
      );
      const data = (response.data ?? {}) as Record<string, unknown>;
      const code = data.patient_code ?? data.code;
      if (!code) throw new Error("no patient code");
      return {
        patient_code: String(code),
        message: String(data.message ?? "Patient registered."),
      };
    },
    {
      patient_code: `PT-${Math.floor(100000 + Math.random() * 899999)}`,
      message: "Sample registration recorded (no live backend response).",
    },
    SAMPLE_NOTE,
  );
}

/**
 * Mark a queued patient as checked in. There is no dedicated reception check-in
 * endpoint yet, so this is a labeled sample action that echoes the new state.
 */
export async function checkInPatient(
  _ctx: Ctx,
  entryId: string,
): Promise<Sourced<{ id: string; status: string }>> {
  void _ctx;
  return {
    value: { id: entryId, status: "CHECKED_IN" },
    source: "sample",
    note: "Check-in recorded locally — no dedicated backend check-in endpoint yet.",
  };
}
