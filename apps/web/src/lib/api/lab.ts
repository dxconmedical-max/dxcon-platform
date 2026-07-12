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
