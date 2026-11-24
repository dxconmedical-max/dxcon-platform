import { API_BASE_URL } from "@/lib/constants";
import { ApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";

type Ctx = { token: string; organizationId?: string | null };
const BASE = "/api/v1/reception/workspace/clinic-billing";

function opts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000, ...extra };
}

export type Aging = { current: number; d1_30: number; d31_60: number; d60_plus: number };

export type Summary = {
  billed: number;
  paid: number;
  outstanding: number;
  credit: number;
  unbilled_orders: number;
  unbilled_amount: number;
  aging: Aging;
};

export type ReceivableRow = Summary & { organization_id: string; organization_name: string; has_activity: boolean };

export type Contract = {
  id: string;
  contract_no: string | null;
  title: string;
  signed_date: string | null;
  start_date: string | null;
  end_date: string | null;
  note: string | null;
  file_name: string | null;
  has_file: boolean;
};

export type Statement = {
  id: string;
  statement_no: string;
  period_start: string;
  period_end: string;
  order_count: number;
  total_amount: number;
  due_date: string;
  paid: number;
  outstanding: number;
  note: string | null;
};

export type Payment = {
  id: string;
  amount: number;
  paid_at: string;
  method: string | null;
  reference: string | null;
  note: string | null;
};

export type ClinicBilling = {
  clinic: { id: string; name: string; code: string };
  settings: { default_discount_pct: number; payment_terms_days: number };
  price_count: number;
  summary: Summary;
  contracts: Contract[];
  statements: Statement[];
  payments: Payment[];
};

export type PriceRow = { id: string; code: string; name: string; list_price: number; clinic_price: number | null };

export type StatementDetail = {
  statement_no: string;
  clinic_name: string;
  period_start: string;
  period_end: string;
  due_date: string;
  total_amount: number;
  lines: { order_code: string; patient_name: string | null; amount: number; ordered_at: string | null }[];
};

export async function getReceivables(ctx: Ctx) {
  const r = await apiRequest<{ data: { clinics: ReceivableRow[]; total_outstanding: number; total_unbilled: number } }>(
    `${BASE}/receivables`,
    opts(ctx),
  );
  return r.data;
}

export async function getClinicBilling(ctx: Ctx, orgId: string): Promise<ClinicBilling> {
  const r = await apiRequest<{ data: ClinicBilling }>(`${BASE}/${encodeURIComponent(orgId)}`, opts(ctx));
  return r.data;
}

export async function saveSettings(ctx: Ctx, orgId: string, body: { default_discount_pct: number; payment_terms_days: number }) {
  await apiRequest(`${BASE}/${encodeURIComponent(orgId)}/settings`, opts(ctx, { method: "POST", body }));
}

export async function listClinicPrices(ctx: Ctx, orgId: string, q: string, custom: boolean): Promise<PriceRow[]> {
  const r = await apiRequest<{ data: PriceRow[] }>(
    `${BASE}/${encodeURIComponent(orgId)}/prices?q=${encodeURIComponent(q)}${custom ? "&custom=1" : ""}`,
    opts(ctx),
  );
  return r.data ?? [];
}

export async function setClinicPrice(ctx: Ctx, orgId: string, testId: string, price: number | null) {
  await apiRequest(`${BASE}/${encodeURIComponent(orgId)}/prices/${encodeURIComponent(testId)}`, opts(ctx, { method: "POST", body: { price } }));
}

export type BulkPriceResult = {
  applied: boolean;
  created: number;
  updated: number;
  removed: number;
  errors: { line: number; code: string; error: string }[];
};

export async function bulkSetPrices(ctx: Ctx, orgId: string, text: string, apply: boolean): Promise<BulkPriceResult> {
  const r = await apiRequest<{ data: BulkPriceResult }>(
    `${BASE}/${encodeURIComponent(orgId)}/prices/bulk`,
    opts(ctx, { method: "POST", body: { text, apply } }),
  );
  return r.data;
}

export async function previewStatement(ctx: Ctx, orgId: string, body: { period_start: string; period_end: string }) {
  const r = await apiRequest<{ data: { order_count: number; total_amount: number } }>(
    `${BASE}/${encodeURIComponent(orgId)}/statements/preview`,
    opts(ctx, { method: "POST", body }),
  );
  return r.data;
}

export async function createStatement(ctx: Ctx, orgId: string, body: { period_start: string; period_end: string; note?: string }) {
  await apiRequest(`${BASE}/${encodeURIComponent(orgId)}/statements`, opts(ctx, { method: "POST", body }));
}

export async function getStatement(ctx: Ctx, orgId: string, id: string): Promise<StatementDetail> {
  const r = await apiRequest<{ data: StatementDetail }>(`${BASE}/${encodeURIComponent(orgId)}/statements/${encodeURIComponent(id)}`, opts(ctx));
  return r.data;
}

export async function voidStatement(ctx: Ctx, orgId: string, id: string) {
  await apiRequest(`${BASE}/${encodeURIComponent(orgId)}/statements/${encodeURIComponent(id)}/void`, opts(ctx, { method: "POST", body: {} }));
}

export async function addPayment(
  ctx: Ctx,
  orgId: string,
  body: { amount: number; paid_at?: string; method?: string; reference?: string; note?: string },
) {
  await apiRequest(`${BASE}/${encodeURIComponent(orgId)}/payments`, opts(ctx, { method: "POST", body }));
}

function authHeaders(ctx: Ctx): Record<string, string> {
  const h: Record<string, string> = { Authorization: `Bearer ${ctx.token}` };
  if (ctx.organizationId) h["X-Organization-ID"] = ctx.organizationId;
  return h;
}

async function failFrom(res: Response): Promise<never> {
  let message = `Request failed (${res.status})`;
  try {
    const j = (await res.json()) as { error?: unknown };
    if (typeof j.error === "string") message = j.error;
  } catch {
    /* keep default message */
  }
  throw new ApiError(message, res.status, {});
}

export async function uploadContract(ctx: Ctx, orgId: string, form: FormData): Promise<void> {
  const res = await fetch(`${API_BASE_URL}${BASE}/${encodeURIComponent(orgId)}/contracts`, {
    method: "POST",
    headers: authHeaders(ctx),
    body: form,
  });
  if (!res.ok) await failFrom(res);
}

export async function downloadContract(ctx: Ctx, orgId: string, contract: Contract): Promise<void> {
  const res = await fetch(`${API_BASE_URL}${BASE}/${encodeURIComponent(orgId)}/contracts/${encodeURIComponent(contract.id)}/file`, {
    headers: authHeaders(ctx),
  });
  if (!res.ok) await failFrom(res);
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = contract.file_name ?? "hop-dong";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
