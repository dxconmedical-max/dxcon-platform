import { apiRequest } from "@/services/api";

export type BoardOrder = {
  order_code: string;
  patient_name: string;
  status: string;
  total_amount: number;
  created_at: string | null;
  source_org_name?: string | null;
};

export type BoardResponse = {
  orders: BoardOrder[];
  total_rows: number;
  page: number;
  page_size: number;
  summary: {
    orders: number;
    by_status: Record<string, number>;
    orders_value: number;
    collected: number;
  };
};

export type BoardQuery = {
  status?: string;
  q?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
};

export async function fetchBoard(
  ctx: { token: string | null; organizationId: string | null },
  query: BoardQuery,
): Promise<BoardResponse> {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) {
    if (v !== undefined && v !== "") params.set(k, String(v));
  }
  const qs = params.toString();
  const res = await apiRequest<BoardResponse & { data?: BoardResponse }>(
    `/api/v1/ops-board/orders${qs ? `?${qs}` : ""}`,
    { token: ctx.token, organizationId: ctx.organizationId },
  );
  return res.data ?? res;
}

type Ctx = { token: string | null; organizationId: string | null };

export type BoardCollection = {
  id: string;
  order_code: string | null;
  patient_name: string | null;
  contact_phone: string | null;
  address: string | null;
  requested_date: string | null;
  time_window: string | null;
  status: string;
  collector_id: string | null;
  collector_name: string | null;
  collector_online: boolean;
  collector_last_seen: string | null;
  created_at: string | null;
};

export type CollectionsResponse = {
  items: BoardCollection[];
  summary: { total: number; unassigned: number; by_status: Record<string, number> };
};

export async function fetchBoardCollections(ctx: Ctx, status = ""): Promise<CollectionsResponse> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await apiRequest<CollectionsResponse & { data?: CollectionsResponse }>(
    `/api/v1/ops-board/collections${qs}`,
    { token: ctx.token, organizationId: ctx.organizationId },
  );
  return res.data ?? res;
}

export type ReportDay = { date: string; orders: number; orders_value: number; collected: number };
export type ReportResponse = {
  days: ReportDay[];
  totals: { orders: number; orders_value: number; collected: number };
  date_from: string;
  date_to: string;
};

export async function fetchReport(ctx: Ctx, dateFrom = "", dateTo = ""): Promise<ReportResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const qs = params.toString() ? `?${params}` : "";
  const res = await apiRequest<ReportResponse & { data?: ReportResponse }>(
    `/api/v1/ops-board/report${qs}`,
    { token: ctx.token, organizationId: ctx.organizationId },
  );
  return res.data ?? res;
}
