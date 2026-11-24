import { apiRequest } from "@/services/api";

type Ctx = { token: string; organizationId?: string | null };

export type DailyPoint = { date: string; orders?: number; revenue?: number; patients?: number };

export type ExecutiveDashboard = {
  widgets: {
    revenue_today: number;
    revenue_this_month: number;
    orders_today: number;
    orders_this_month: number;
    patients: number;
    pending_reports: number;
    critical_results: number;
    sample_collections: number;
  };
  charts: {
    revenue_trend: DailyPoint[];
    order_trend: DailyPoint[];
    top_tests: { test_name: string; count: number }[];
    laboratory_performance: {
      tat_hours_avg: number | null;
      sample_size?: number;
      window_days?: number;
      measured?: boolean;
    };
  };
};

export type ReportSummary = {
  period_start: string;
  period_end: string;
  orders_total: number;
  revenue_total: number;
  orders_by_status: { status: string; count: number }[];
  orders_by_source: { source: string; count: number }[];
  daily: { date: string; orders: number; revenue: number }[];
  top_tests: { test_name: string; quantity: number; revenue: number }[];
};

function opts(ctx: Ctx) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000 };
}

export async function fetchExecutiveDashboard(ctx: Ctx): Promise<ExecutiveDashboard> {
  const response = await apiRequest<{ success: boolean; data: ExecutiveDashboard }>(
    "/api/v1/executive-platform/dashboard",
    opts(ctx),
  );
  return response.data;
}

export async function fetchReportSummary(
  ctx: Ctx,
  range: { from?: string; to?: string } = {},
): Promise<ReportSummary> {
  const params = new URLSearchParams();
  if (range.from) params.set("date_from", range.from);
  if (range.to) params.set("date_to", range.to);
  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await apiRequest<{ success: boolean; data: ReportSummary }>(
    `/api/v1/executive-platform/report/summary${query}`,
    opts(ctx),
  );
  return response.data;
}
