import { apiRequest, type ApiEnvelope } from "@/lib/api/client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "@/lib/api/adapter";

type Ctx = { token: string; organizationId: string };

export type TechnicianQueue = {
  preliminary_analyzer: Array<Record<string, unknown>>;
  result_items_pending: Array<Record<string, unknown>>;
};

export type ResultItemDetail = Record<string, unknown> & {
  id: string;
  test_code?: string;
  result_status?: string;
  original_value?: string;
  normalized_value?: string;
};

export async function fetchTechnicianQueue(ctx: Ctx): Promise<Sourced<TechnicianQueue>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<TechnicianQueue>>("/api/v1/clinical/technician/queue", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      if (!res.data) throw new Error("no queue");
      return res.data;
    },
    { preliminary_analyzer: [], result_items_pending: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchTechnicianResult(ctx: Ctx, itemId: string): Promise<Sourced<ResultItemDetail>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<ResultItemDetail>>(
        `/api/v1/clinical/technician/results/${encodeURIComponent(itemId)}`,
        { token: ctx.token, organizationId: ctx.organizationId },
      );
      if (!res.data) throw new Error("not found");
      return res.data;
    },
    { id: itemId, result_status: "PENDING" },
    SAMPLE_NOTE,
  );
}

export async function validateResult(ctx: Ctx, itemId: string, note?: string): Promise<void> {
  await apiRequest(`/api/v1/clinical/technician/results/${encodeURIComponent(itemId)}/validate`, {
    method: "POST",
    token: ctx.token,
    organizationId: ctx.organizationId,
    body: { note },
  });
}

export async function rejectResult(ctx: Ctx, itemId: string, reason: string): Promise<void> {
  await apiRequest(`/api/v1/clinical/technician/results/${encodeURIComponent(itemId)}/reject`, {
    method: "POST",
    token: ctx.token,
    organizationId: ctx.organizationId,
    body: { reason },
  });
}

export async function fetchDoctorClinicalQueue(ctx: Ctx): Promise<Sourced<{ data: Record<string, unknown>[] }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ data: Record<string, unknown>[] }>>("/api/v1/clinical/doctor/queue", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      return res.data ?? { data: [] };
    },
    { data: [] },
    SAMPLE_NOTE,
  );
}

export async function verifyReportToken(token: string): Promise<Record<string, unknown>> {
  const res = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    `/api/v1/verify-report/${encodeURIComponent(token)}`,
  );
  return res.data ?? { valid: false };
}
