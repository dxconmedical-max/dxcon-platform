import { apiRequest } from "@/services/api";
import { ApiError } from "@/lib/errors";

export type LabAuth = {
  token?: string | null;
  organizationId?: string | null;
};

export type LabDashboard = {
  kpis: {
    incoming: number;
    received: number;
    testing: number;
    pending_validation: number;
    pending_review: number;
    released_today: number;
    failed_imports: number;
    abnormal_results: number;
    rejected?: number;
  };
  status_contract?: LabStatusContract;
  incoming_samples?: LabQueueRow[];
  testing_queue?: LabQueueRow[];
  accession_queue?: Record<string, unknown>[];
  pending_review?: Record<string, unknown>[];
};

export type LabStatusContract = {
  order_flow: string[];
  exceptions: string[];
  processing: string[];
  result_workflow: string[];
  condition_statuses: string[];
  rejection_reasons: string[];
  accession_id_format: string;
};

export type LabQueueRow = {
  order_code: string;
  patient?: string;
  patient_name?: string;
  patient_code?: string;
  sample_code?: string | null;
  accession_number?: string | null;
  status?: string;
  order_status?: string;
  processing_status?: string | null;
  test_code?: string;
  test_name?: string;
  bench_id?: string | null;
  instrument_id?: string | null;
  technician?: string | null;
  workflow_status?: string | null;
  [key: string]: unknown;
};

export type LabOrderWorkspace = {
  order: Record<string, unknown>;
  collection: Record<string, unknown> | null;
  accession: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  audits: Record<string, unknown>[];
  locked: boolean;
  status_contract?: LabStatusContract;
};

export const REJECTION_REASON_OPTIONS = [
  { value: "hemolyzed", label: "Hemolyzed" },
  { value: "insufficient_volume", label: "Insufficient volume" },
  { value: "wrong_tube", label: "Wrong tube" },
  { value: "damaged", label: "Damaged" },
  { value: "clotted", label: "Clotted" },
  { value: "mislabeled", label: "Mislabeled" },
  { value: "patient_mismatch", label: "Patient mismatch" },
  { value: "order_mismatch", label: "Order mismatch" },
  { value: "expired", label: "Expired" },
  { value: "other", label: "Other" },
] as const;

function opts(auth: LabAuth, extra?: { timeoutMs?: number; signal?: AbortSignal }) {
  return {
    token: auth.token,
    organizationId: auth.organizationId,
    timeoutMs: extra?.timeoutMs,
    signal: extra?.signal,
  };
}

async function unwrap<T>(promise: Promise<{ success?: boolean; data?: T; error?: string }>): Promise<T> {
  const body = await promise;
  if (body && body.success === false) {
    throw new ApiError(body.error || "Laboratory request failed", 400);
  }
  if (body?.data === undefined) {
    throw new ApiError("Empty laboratory response", 500);
  }
  return body.data;
}

export async function fetchLabDashboard(auth: LabAuth): Promise<LabDashboard> {
  return unwrap(
    apiRequest<{ success?: boolean; data?: LabDashboard; error?: string }>(
      "/api/v1/lab/workspace/dashboard",
      opts(auth),
    ),
  );
}

export async function fetchLabStatusContract(auth: LabAuth): Promise<LabStatusContract> {
  return unwrap(
    apiRequest<{ success?: boolean; data?: LabStatusContract; error?: string }>(
      "/api/v1/lab/workspace/status-contract",
      opts(auth),
    ),
  );
}

export async function fetchTestingQueue(
  auth: LabAuth,
  params?: { page?: number; per_page?: number; status?: string },
): Promise<{ data: LabQueueRow[]; pagination: Record<string, number> }> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.per_page) qs.set("per_page", String(params.per_page));
  if (params?.status) qs.set("status", params.status);
  const q = qs.toString();
  const body = await apiRequest<{
    success?: boolean;
    data?: LabQueueRow[];
    pagination?: Record<string, number>;
    error?: string;
  }>(`/api/v1/lab/workspace/testing-queue${q ? `?${q}` : ""}`, opts(auth));
  if (body.success === false) throw new ApiError(body.error || "Queue failed", 400);
  return { data: body.data ?? [], pagination: body.pagination ?? { page: 1, per_page: 50, total: 0 } };
}

export async function fetchLabOrder(auth: LabAuth, orderCode: string): Promise<LabOrderWorkspace> {
  return unwrap(
    apiRequest<{ success?: boolean; data?: LabOrderWorkspace; error?: string }>(
      `/api/v1/lab/workspace/orders/${encodeURIComponent(orderCode)}`,
      opts(auth),
    ),
  );
}

export async function verifyLabIdentifiers(
  auth: LabAuth,
  payload: {
    order_code?: string;
    sample_code?: string;
    barcode_value?: string;
    patient_code?: string;
  },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/verify",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function receiveSpecimen(
  auth: LabAuth,
  payload: {
    order_code?: string;
    sample_code?: string;
    patient_code?: string;
    barcode_value?: string;
    condition_status?: string;
    rejection_reason?: string;
    note?: string;
    received_by?: string;
  },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/receive",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function rejectSpecimen(
  auth: LabAuth,
  payload: {
    order_code?: string;
    sample_code?: string;
    rejection_reason: string;
    note?: string;
  },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/reject",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function createAccession(
  auth: LabAuth,
  payload: { order_code: string; sample_code?: string; accessioned_by?: string },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/accession",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function assignBench(
  auth: LabAuth,
  payload: {
    order_code: string;
    bench_id?: string;
    instrument_id?: string;
    technician?: string;
  },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/assign",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function startProcessing(auth: LabAuth, order_code: string) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/processing/start",
      { ...opts(auth), method: "POST", body: { order_code } },
    ),
  );
}

export async function enterLabResult(
  auth: LabAuth,
  payload: {
    order_code: string;
    test_code: string;
    result_value: string;
    unit?: string;
    reference_range?: string;
    critical_low?: number;
    critical_high?: number;
    instrument?: string;
    technician?: string;
    note?: string;
    revision_mode?: boolean;
  },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/results",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function ingestAnalyzerResult(
  auth: LabAuth,
  payload: {
    order_code: string;
    test_code: string;
    result_value: string;
    unit?: string;
    reference_range?: string;
    instrument?: string;
  },
) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/results/ingest",
      { ...opts(auth), method: "POST", body: payload },
    ),
  );
}

export async function passQc(auth: LabAuth, order_code: string, note?: string) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/qc/pass",
      { ...opts(auth), method: "POST", body: { order_code, note } },
    ),
  );
}

export async function technicalValidate(auth: LabAuth, order_code: string) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/validation/approve",
      { ...opts(auth), method: "POST", body: { order_code } },
    ),
  );
}

export async function rejectTechValidation(auth: LabAuth, order_code: string, reason?: string) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/validation/reject",
      { ...opts(auth), method: "POST", body: { order_code, reason } },
    ),
  );
}

export async function medicalValidate(auth: LabAuth, order_code: string, doctor_note?: string) {
  return unwrap(
    apiRequest<{ success?: boolean; data?: Record<string, unknown>; error?: string }>(
      "/api/v1/lab/workspace/medical-validation/approve",
      { ...opts(auth), method: "POST", body: { order_code, doctor_note } },
    ),
  );
}
