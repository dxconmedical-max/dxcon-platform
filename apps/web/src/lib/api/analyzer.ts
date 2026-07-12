import { apiRequest, type ApiEnvelope } from "@/lib/api/client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "@/lib/api/adapter";

type Ctx = { token: string; organizationId: string };

export type AnalyzerSummary = {
  id: string;
  analyzer_code: string;
  name: string;
  status: string;
  protocol?: string;
};

export type AnalyzerDashboard = {
  kpis: {
    analyzers_online: number;
    pending_review: number;
    quarantine_open: number;
    worklist_queued: number;
  };
};

export type PreliminaryResult = {
  id: string;
  specimen_barcode?: string;
  test_code?: string;
  original_value: string;
  normalized_value?: string;
  unit?: string;
  review_status: string;
  auto_released: boolean;
};

export type QuarantineItem = {
  id: string;
  reason_code: string;
  reason_detail?: string;
  specimen_barcode?: string;
  status: string;
};

export async function fetchAnalyzerDashboard(ctx: Ctx): Promise<Sourced<AnalyzerDashboard>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<AnalyzerDashboard>>("/api/v1/lab/analyzer-dashboard", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      if (!res.data?.kpis) throw new Error("no dashboard");
      return res.data;
    },
    { kpis: { analyzers_online: 0, pending_review: 0, quarantine_open: 0, worklist_queued: 0 } },
    SAMPLE_NOTE,
  );
}

export async function fetchAnalyzers(ctx: Ctx): Promise<Sourced<{ analyzers: AnalyzerSummary[] }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ analyzers: AnalyzerSummary[] }>>("/api/v1/analyzers", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      return res.data ?? { analyzers: [] };
    },
    { analyzers: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchResultReview(ctx: Ctx): Promise<Sourced<{ results: PreliminaryResult[] }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ results: PreliminaryResult[] }>>(
        "/api/v1/lab/result-review",
        { token: ctx.token, organizationId: ctx.organizationId },
      );
      return res.data ?? { results: [] };
    },
    { results: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchQuarantineQueue(ctx: Ctx): Promise<Sourced<{ items: QuarantineItem[] }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ items: QuarantineItem[] }>>(
        "/api/v1/integrations/analyzer/quarantine",
        { token: ctx.token, organizationId: ctx.organizationId },
      );
      return res.data ?? { items: [] };
    },
    { items: [] },
    SAMPLE_NOTE,
  );
}
