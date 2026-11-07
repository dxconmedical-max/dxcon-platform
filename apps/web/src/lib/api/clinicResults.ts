import { apiRequest } from "@/services/api";

export type ClinicReportSummary = {
  order_code: string;
  result_code: string;
  patient_code: string;
  patient_name: string;
  released_at: string | null;
};

export type ClinicReportDetail = ClinicReportSummary & {
  html_content: string;
};

type Ctx = { token: string; organizationId?: string | null };

function opts(ctx: Ctx) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000 };
}

export async function listClinicReports(
  ctx: Ctx,
  page = 1,
  limit = 50,
): Promise<{ items: ClinicReportSummary[]; total: number }> {
  const response = await apiRequest<{
    success: boolean;
    data: ClinicReportSummary[];
    pagination?: { total?: number };
  }>(`/api/v1/clinic-results/reports?page=${page}&limit=${limit}`, opts(ctx));
  const items = response.data ?? [];
  return { items, total: response.pagination?.total ?? items.length };
}

export async function getClinicReport(
  ctx: Ctx,
  orderCode: string,
): Promise<ClinicReportDetail> {
  const response = await apiRequest<{ success: boolean; data: ClinicReportDetail }>(
    `/api/v1/clinic-results/reports/${encodeURIComponent(orderCode)}`,
    opts(ctx),
  );
  return response.data;
}
