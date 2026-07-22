import { apiRequest, type ApiEnvelope } from "./client";
import type { Sourced } from "./adapter";

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
  email?: string;
  address?: string;
  national_id?: string;
  note?: string;
};

export type ReceptionPatient = {
  patient_code: string;
  full_name: string;
  phone?: string | null;
  national_id?: string | null;
  email?: string | null;
  address?: string | null;
  gender?: string | null;
  date_of_birth?: string | null;
  qr_payload?: string;
};

export type ReceptionTest = {
  id: string;
  code: string;
  name: string;
  category?: string | null;
  sample_type?: string | null;
  price?: number | null;
};

export type ReceptionOrderPricing = {
  subtotal: number;
  discount: number;
  total: number;
};

export type ReceptionOrderCreate = {
  order: Record<string, unknown>;
  invoice: Record<string, unknown>;
  pricing: ReceptionOrderPricing;
};

type Ctx = { token: string; organizationId: string };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

function listRowsFromEnvelope(body: Record<string, unknown>): Record<string, unknown>[] {
  if (Array.isArray(body.data)) {
    return body.data as Record<string, unknown>[];
  }
  const nested = body.data;
  if (nested && typeof nested === "object" && Array.isArray((nested as Record<string, unknown>).data)) {
    return (nested as Record<string, unknown>).data as Record<string, unknown>[];
  }
  return [];
}

function paginationTotal(body: Record<string, unknown>, fallback: number): number {
  const top = body.pagination as { total?: number } | undefined;
  if (top?.total != null) return top.total;
  const nested = body.data;
  if (nested && typeof nested === "object") {
    const nestedPagination = (nested as Record<string, unknown>).pagination as { total?: number } | undefined;
    if (nestedPagination?.total != null) return nestedPagination.total;
  }
  return fallback;
}

function mapQueue(rows: Record<string, unknown>[]): QueueEntry[] {
  return rows.map((row) => {
    const status = String(row.workflow_status ?? row.status ?? "WAITING").toUpperCase();
    return {
      id: String(row.id ?? row.queue_entry_id ?? row.order_ref ?? "—"),
      patient_name: String(row.patient_name ?? row.full_name ?? row.name ?? "—"),
      patient_code: row.patient_code
        ? String(row.patient_code)
        : row.patient_id
          ? String(row.patient_id)
          : undefined,
      service: String(row.service ?? row.test ?? row.description ?? "—"),
      checked_in: status === "CHECKED_IN" || Boolean(row.checked_in),
      arrived_at: row.arrived_at
        ? String(row.arrived_at)
        : row.created_at
          ? String(row.created_at)
          : undefined,
      status,
    };
  });
}

/** Today's reception queue. GET /api/v1/reception/workspace/queue */
export async function fetchReceptionQueue({
  token,
  organizationId,
}: Ctx): Promise<Sourced<QueueEntry[]>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    "/api/v1/reception/workspace/queue",
    { token, organizationId },
  );
  const raw = asArray(response.data?.queue ?? response.data?.workflow_queue ?? response.data);
  return { value: mapQueue(raw), source: "live" };
}

/** Patient search. GET /api/v1/reception/workspace/search */
export async function searchReceptionPatients(
  { token, organizationId }: Ctx,
  query: string,
): Promise<{ items: ReceptionPatient[]; total: number }> {
  const params = new URLSearchParams({ q: query, limit: "25" });
  const response = await apiRequest<Record<string, unknown>>(
    `/api/v1/reception/workspace/search?${params}`,
    { token, organizationId },
  );
  const raw = listRowsFromEnvelope(response);
  return {
    items: raw.map((p) => ({
      patient_code: String(p.patient_code ?? p.id ?? "—"),
      full_name: String(p.full_name ?? "—"),
      phone: p.phone ? String(p.phone) : null,
      national_id: p.national_id ? String(p.national_id) : null,
      email: p.email ? String(p.email) : null,
      address: p.address ? String(p.address) : null,
      gender: p.gender ? String(p.gender) : null,
      date_of_birth: p.date_of_birth ? String(p.date_of_birth) : null,
      qr_payload: p.qr_payload ? String(p.qr_payload) : undefined,
    })),
    total: paginationTotal(response, raw.length),
  };
}

/** Compatibility wrapper used by older queue/search callers. */
export async function searchReception(
  ctx: Ctx,
  query: string,
): Promise<Sourced<QueueEntry[]>> {
  const result = await searchReceptionPatients(ctx, query);
  return {
    value: result.items.map((patient) => ({
      id: patient.patient_code,
      patient_name: patient.full_name,
      patient_code: patient.patient_code,
      checked_in: false,
      status: "WAITING",
    })),
    source: "live",
  };
}

/** Walk-in registration. POST /api/v1/reception/workspace/patients/register */
export async function registerWalkIn(
  { token, organizationId }: Ctx,
  registration: WalkInRegistration,
): Promise<Sourced<{ patient_code: string; message: string; patient?: ReceptionPatient }>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    "/api/v1/reception/workspace/patients/register",
    { token, organizationId, method: "POST", body: registration },
  );
  const data = (response.data ?? {}) as Record<string, unknown>;
  const patient =
    data.patient && typeof data.patient === "object"
      ? (data.patient as Record<string, unknown>)
      : data;
  const code = patient.patient_code ?? data.patient_code ?? data.code;
  if (!code) {
    throw new Error("Patient registration did not return a patient code");
  }
  return {
    value: {
      patient_code: String(code),
      message: String(data.message ?? "Patient registered."),
      patient: {
        patient_code: String(code),
        full_name: String(patient.full_name ?? registration.full_name),
        phone: patient.phone ? String(patient.phone) : registration.phone,
        national_id: patient.national_id ? String(patient.national_id) : registration.national_id ?? null,
      },
    },
    source: "live",
  };
}

/** Queue check-in. POST /api/v1/reception/workspace/queue/:id/check-in */
export async function checkInPatient(
  { token, organizationId }: Ctx,
  entryId: string,
): Promise<Sourced<{ id: string; status: string }>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    `/api/v1/reception/workspace/queue/${encodeURIComponent(entryId)}/check-in`,
    { token, organizationId, method: "POST", body: {} },
  );
  const data = (response.data ?? {}) as Record<string, unknown>;
  const status = String(data.status ?? data.workflow_status ?? "CHECKED_IN").toUpperCase();
  return {
    value: { id: String(data.id ?? entryId), status },
    source: "live",
  };
}

/** Test catalog. GET /api/v1/reception/workspace/tests */
export async function fetchReceptionTests(
  { token, organizationId }: Ctx,
  params: { q?: string; category?: string; limit?: number } = {},
): Promise<{ items: ReceptionTest[]; total: number }> {
  const qs = new URLSearchParams();
  qs.set("limit", String(params.limit ?? 100));
  qs.set("page", "1");
  if (params.q) qs.set("q", params.q);
  if (params.category) qs.set("category", params.category);

  const response = await apiRequest<Record<string, unknown>>(
    `/api/v1/reception/workspace/tests?${qs}`,
    { token, organizationId },
  );
  const raw = listRowsFromEnvelope(response);
  return {
    items: raw.map((t) => ({
      id: String(t.id),
      code: String(t.code),
      name: String(t.name),
      category: t.category ? String(t.category) : null,
      sample_type: t.sample_type ? String(t.sample_type) : null,
      price: t.price != null ? Number(t.price) : null,
    })),
    total: paginationTotal(response, raw.length),
  };
}

/** Create order. POST /api/v1/reception/workspace/orders */
export async function createReceptionOrder(
  { token, organizationId }: Ctx,
  payload: {
    patient_code: string;
    test_catalog_ids: string[];
    discount?: number;
    note?: string;
    queue_entry_id?: string;
  },
): Promise<ReceptionOrderCreate> {
  const response = await apiRequest<ApiEnvelope<ReceptionOrderCreate>>(
    "/api/v1/reception/workspace/orders",
    {
      token,
      organizationId,
      method: "POST",
      body: {
        patient_code: payload.patient_code,
        test_catalog_ids: payload.test_catalog_ids,
        discount: payload.discount ?? 0,
        note: payload.note,
        queue_entry_id: payload.queue_entry_id,
      },
    },
  );
  return response.data;
}

export function getOrderCode(order: ReceptionOrderCreate["order"] | null | undefined): string {
  if (!order) return "";
  const row = order as Record<string, unknown>;
  const code = row.order_code ?? row.orderRef ?? row.id;
  return code ? String(code) : "";
}
