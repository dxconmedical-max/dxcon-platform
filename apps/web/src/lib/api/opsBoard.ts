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
