import { apiRequest, type ApiEnvelope } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";
import {
  SAMPLE_LAB_SAMPLES,
  SAMPLE_QC,
  SAMPLE_VERIFICATION,
} from "./samples";

export type LabSample = {
  sample_code: string;
  order_code?: string;
  test?: string;
  received_at?: string;
  condition?: string;
  status: string;
};

export type QcItem = {
  sample_code: string;
  test?: string;
  control_lot?: string;
  status: string;
  note?: string;
};

export type VerificationItem = {
  order_code: string;
  test?: string;
  result_value?: string;
  abnormal: boolean;
  status: string;
};

type Ctx = { token: string; organizationId: string };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

/** Analyzer / testing queue. Backed by GET /lab/workspace/testing-queue. */
export async function fetchAnalyzerQueue({
  token,
  organizationId,
}: Ctx): Promise<Sourced<LabSample[]>> {
  return withSampleFallback<LabSample[]>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/lab/workspace/testing-queue",
        { token, organizationId },
      );
      const raw = asArray(response.data?.queue ?? response.data?.items ?? response.data);
      const samples = raw.map((row) => ({
        sample_code: String(row.sample_code ?? row.sample_id ?? row.barcode ?? row.id ?? "—"),
        order_code: row.order_code ? String(row.order_code) : undefined,
        test: String(row.test ?? row.test_name ?? row.panel ?? "—"),
        received_at: row.received_at ? String(row.received_at) : undefined,
        condition: row.condition ? String(row.condition) : undefined,
        status: String(row.status ?? "IN_TESTING").toUpperCase(),
      }));
      if (samples.length === 0) throw new Error("empty queue");
      return samples;
    },
    SAMPLE_LAB_SAMPLES.filter((s) => s.status !== "RECEIVED"),
    SAMPLE_NOTE,
  );
}

/** Recently received samples. Sample fallback (no dedicated GET list). */
export async function fetchReceivedSamples(_ctx: Ctx): Promise<Sourced<LabSample[]>> {
  void _ctx;
  return { value: SAMPLE_LAB_SAMPLES, source: "sample", note: SAMPLE_NOTE };
}

/** QC status list. Labeled sample adapter (no GET QC list endpoint). */
export async function fetchQcStatus(_ctx: Ctx): Promise<Sourced<QcItem[]>> {
  void _ctx;
  return { value: SAMPLE_QC, source: "sample", note: SAMPLE_NOTE };
}

/** Results awaiting verification. Labeled sample adapter. */
export async function fetchVerificationQueue(_ctx: Ctx): Promise<Sourced<VerificationItem[]>> {
  void _ctx;
  return { value: SAMPLE_VERIFICATION, source: "sample", note: SAMPLE_NOTE };
}

/** Approve (verify) a result. Backed by POST /lab/workspace/validation/approve. */
export async function verifyResult(
  { token, organizationId }: Ctx,
  orderCode: string,
): Promise<Sourced<{ order_code: string; status: string }>> {
  return withSampleFallback<{ order_code: string; status: string }>(
    async () => {
      await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/lab/workspace/validation/approve",
        { token, organizationId, method: "POST", body: { order_code: orderCode } },
      );
      return { order_code: orderCode, status: "VERIFIED" };
    },
    { order_code: orderCode, status: "VERIFIED" },
    "Verification recorded locally (no live backend response).",
  );
}

/** Release a verified result. Backed by POST /reporting/review/<ref>/release. */
export async function releaseResult(
  { token, organizationId }: Ctx,
  orderCode: string,
): Promise<Sourced<{ order_code: string; status: string }>> {
  return withSampleFallback<{ order_code: string; status: string }>(
    async () => {
      await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        `/api/v1/reporting/review/${encodeURIComponent(orderCode)}/release`,
        { token, organizationId, method: "POST", body: {} },
      );
      return { order_code: orderCode, status: "RELEASED" };
    },
    { order_code: orderCode, status: "RELEASED" },
    "Release recorded locally (no live backend response).",
  );
}

// --- LIMS Core (Release 7.0) ---

export type LimsSpecimen = {
  id: string;
  barcode: string;
  human_readable: string;
  order_code?: string;
  patient_code?: string;
  status: string;
  container_type?: string;
  volume?: number;
  volume_unit?: string;
  collected_at?: string;
  expires_at?: string;
};

export type LimsTimelineEvent = {
  id: string;
  specimen_id: string;
  from_status?: string;
  to_status: string;
  actor?: string;
  note?: string;
  transitioned_at: string;
};

export type LimsDashboard = {
  kpis: Record<string, number>;
  cards: { label: string; value: number }[];
};

/** LIMS realtime dashboard — GET /api/v1/lab/dashboard */
export async function fetchLimsDashboard({ token, organizationId }: Ctx): Promise<Sourced<LimsDashboard>> {
  return withSampleFallback<LimsDashboard>(
    async () => {
      const response = await apiRequest<ApiEnvelope<LimsDashboard>>("/api/v1/lab/dashboard", {
        token,
        organizationId,
      });
      if (!response.data?.kpis) throw new Error("no dashboard");
      return response.data;
    },
    {
      kpis: {
        samples_today: 0,
        pending_collection: 0,
        in_transit: 0,
        received: 0,
        processing: 0,
        qc_failed: 0,
        validation_pending: 0,
        released_today: 0,
      },
      cards: [],
    },
    SAMPLE_NOTE,
  );
}

export async function fetchSpecimens(
  { token, organizationId }: Ctx,
  page = 1,
  status?: string,
): Promise<Sourced<{ items: LimsSpecimen[]; total: number }>> {
  const params = new URLSearchParams({ page: String(page), per_page: "25" });
  if (status) params.set("status", status);
  return withSampleFallback(
    async () => {
      const response = await apiRequest<ApiEnvelope<{ items: LimsSpecimen[]; pagination: { total: number } }>>(
        `/api/v1/specimens?${params}`,
        { token, organizationId },
      );
      const items = response.data?.items ?? [];
      return { items, total: response.data?.pagination?.total ?? items.length };
    },
    { items: [], total: 0 },
    SAMPLE_NOTE,
  );
}

export async function fetchSpecimenDetail(
  { token, organizationId }: Ctx,
  specimenId: string,
): Promise<Sourced<LimsSpecimen & { history?: LimsTimelineEvent[] }>> {
  return withSampleFallback(
    async () => {
      const response = await apiRequest<ApiEnvelope<LimsSpecimen & { history?: LimsTimelineEvent[] }>>(
        `/api/v1/specimens/${encodeURIComponent(specimenId)}`,
        { token, organizationId },
      );
      if (!response.data?.id) throw new Error("not found");
      return response.data;
    },
    { id: specimenId, barcode: "", human_readable: "", status: "CREATED" },
    SAMPLE_NOTE,
  );
}

export async function verifySpecimenBarcode(
  { token, organizationId }: Ctx,
  value: string,
): Promise<Sourced<{ valid: boolean; specimen?: LimsSpecimen }>> {
  return withSampleFallback(
    async () => {
      const response = await apiRequest<ApiEnvelope<{ valid: boolean; specimen?: LimsSpecimen }>>(
        `/api/v1/barcodes?value=${encodeURIComponent(value)}`,
        { token, organizationId },
      );
      return response.data ?? { valid: false };
    },
    { valid: false },
    SAMPLE_NOTE,
  );
}

export async function accessionSpecimen(
  { token, organizationId }: Ctx,
  payload: { barcode_value: string; rack?: string; shelf?: string; batch?: string; operator?: string },
): Promise<Sourced<Record<string, unknown>>> {
  return withSampleFallback(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/accessions",
        { token, organizationId, method: "POST", body: payload },
      );
      return response.data ?? {};
    },
    { accession_number: "SAMPLE-ACC", status: "active" },
    SAMPLE_NOTE,
  );
}

export async function fetchSpecimenTimeline(
  { token, organizationId }: Ctx,
  specimenId: string,
): Promise<Sourced<LimsTimelineEvent[]>> {
  return withSampleFallback(
    async () => {
      const response = await apiRequest<ApiEnvelope<LimsTimelineEvent[]>>(
        `/api/v1/specimens/${encodeURIComponent(specimenId)}/timeline`,
        { token, organizationId },
      );
      return Array.isArray(response.data) ? response.data : [];
    },
    [],
    SAMPLE_NOTE,
  );
}
