import { apiRequest } from "@/services/api";

export type PublicResult = {
  patient_name: string;
  order_code: string;
  released_at: string;
  items: Array<{
    test_name: string;
    result_value: string | null;
    unit: string | null;
    reference_range: string | null;
    flag: string | null;
  }>;
};

export type ResultLink = { url: string; qr_png: string | null; expires_days: number };

export async function fetchPublicResult(token: string): Promise<PublicResult> {
  const res = await apiRequest<PublicResult & { data?: PublicResult }>(
    `/api/v1/public/results/${encodeURIComponent(token)}`,
  );
  return res.data ?? res;
}

export async function createResultLink(
  ctx: { token: string | null; organizationId: string | null },
  orderCode: string,
): Promise<ResultLink> {
  const res = await apiRequest<ResultLink & { data?: ResultLink }>(
    `/api/v1/result-links/${encodeURIComponent(orderCode)}`,
    { method: "POST", token: ctx.token, organizationId: ctx.organizationId },
  );
  return res.data ?? res;
}
