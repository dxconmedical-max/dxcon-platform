import { apiRequest } from "@/services/api";

import { downloadFile, uploadSheet, type BulkPriceResult } from "@/lib/api/clinicBilling";

type Ctx = { token: string; organizationId?: string | null };
const BASE = "/api/v1/reception/workspace/lab-payables";

function opts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000, ...extra };
}

export type LabSummary = {
  billed: number;
  paid: number;
  outstanding: number;
  unbilled_orders: number;
  unbilled_cost: number;
  unbilled_margin: number;
  missing_cost_orders: number;
};

export type LabRow = LabSummary & { organization_id: string; organization_name: string; code: string };

export type OrgHit = { id: string; name: string; code: string; type: string };

export type RoutingData = {
  labs: { id: string; name: string }[];
  default_lab_id: string | null;
  clinics: { id: string; name: string; lab_id: string | null }[];
};

export type UnassignedOrder = {
  order_code: string;
  patient_name: string;
  clinic_name: string;
  total_amount: number;
  created_at: string | null;
};

export type CostRow = { id: string; code: string; name: string; list_price: number; cost: number | null };

export type LabStatement = {
  id: string;
  statement_no: string;
  period_start: string;
  period_end: string;
  order_count: number;
  total_amount: number;
  status: string;
  note: string | null;
};

export type LabPayment = { id: string; amount: number; paid_at: string; method: string | null; reference: string | null; note: string | null };

export type LabDetail = {
  lab: { id: string; name: string; code: string };
  summary: LabSummary;
  statements: LabStatement[];
  payments: LabPayment[];
};

export type LabStatementDetail = {
  statement_no: string;
  lab_name: string;
  period_start: string;
  period_end: string;
  total_amount: number;
  status: string;
  lines: { order_code: string; patient_name: string; amount: number }[];
};

export async function getLabs(ctx: Ctx) {
  const r = await apiRequest<{ data: { labs: LabRow[]; total_outstanding: number; total_unbilled: number } }>(`${BASE}/labs`, opts(ctx));
  return r.data;
}

export async function searchOrganizations(ctx: Ctx, q: string) {
  const r = await apiRequest<{ data: OrgHit[] }>(`${BASE}/organizations?q=${encodeURIComponent(q)}`, opts(ctx));
  return r.data;
}

export async function addLab(ctx: Ctx, organizationId: string) {
  await apiRequest(`${BASE}/labs`, opts(ctx, { method: "POST", body: { organization_id: organizationId } }));
}

export async function getRouting(ctx: Ctx) {
  const r = await apiRequest<{ data: RoutingData }>(`${BASE}/routing`, opts(ctx));
  return r.data;
}

export async function setRouting(ctx: Ctx, scope: string, labId: string | null) {
  await apiRequest(`${BASE}/routing`, opts(ctx, { method: "POST", body: { scope_org_id: scope, lab_organization_id: labId ?? "" } }));
}

export async function getUnassigned(ctx: Ctx) {
  const r = await apiRequest<{ data: UnassignedOrder[] }>(`${BASE}/unassigned`, opts(ctx));
  return r.data;
}

export async function assignOrders(ctx: Ctx, labId: string, orderCodes: string[]) {
  const r = await apiRequest<{ data: { assigned: number; locked: number } }>(
    `${BASE}/orders/assign`,
    opts(ctx, { method: "POST", body: { lab_organization_id: labId, order_codes: orderCodes } }),
  );
  return r.data;
}

export async function getLab(ctx: Ctx, labId: string) {
  const r = await apiRequest<{ data: LabDetail }>(`${BASE}/${encodeURIComponent(labId)}`, opts(ctx));
  return r.data;
}

export async function listCosts(ctx: Ctx, labId: string, q: string, onlyPriced: boolean) {
  const r = await apiRequest<{ data: { priced_count: number; tests: CostRow[] } }>(
    `${BASE}/${encodeURIComponent(labId)}/costs?q=${encodeURIComponent(q)}${onlyPriced ? "&custom=1" : ""}`,
    opts(ctx),
  );
  return r.data;
}

export async function bulkSetCosts(ctx: Ctx, labId: string, text: string, apply: boolean): Promise<BulkPriceResult> {
  const r = await apiRequest<{ data: BulkPriceResult }>(
    `${BASE}/${encodeURIComponent(labId)}/costs/bulk`,
    opts(ctx, { method: "POST", body: { text, apply } }),
  );
  return r.data;
}

export async function downloadCostTemplate(ctx: Ctx, labId: string) {
  await downloadFile(ctx, `${BASE}/${encodeURIComponent(labId)}/costs/template`, "gia-nhap.xlsx");
}

export async function uploadCostFile(ctx: Ctx, labId: string, file: File, apply: boolean) {
  return uploadSheet(ctx, `${BASE}/${encodeURIComponent(labId)}/costs/upload`, file, apply);
}

export async function recalcLab(ctx: Ctx, labId: string) {
  const r = await apiRequest<{ data: { recalculated: number } }>(`${BASE}/${encodeURIComponent(labId)}/recalc`, opts(ctx, { method: "POST", body: {} }));
  return r.data;
}

export async function previewLabStatement(ctx: Ctx, labId: string, period: { period_start: string; period_end: string }) {
  const r = await apiRequest<{ data: { order_count: number; total_amount: number; margin: number; missing_cost_orders: number } }>(
    `${BASE}/${encodeURIComponent(labId)}/statements/preview`,
    opts(ctx, { method: "POST", body: period }),
  );
  return r.data;
}

export async function createLabStatement(ctx: Ctx, labId: string, body: { period_start: string; period_end: string; note?: string }) {
  await apiRequest(`${BASE}/${encodeURIComponent(labId)}/statements`, opts(ctx, { method: "POST", body }));
}

export async function getLabStatement(ctx: Ctx, labId: string, statementId: string) {
  const r = await apiRequest<{ data: LabStatementDetail }>(`${BASE}/${encodeURIComponent(labId)}/statements/${encodeURIComponent(statementId)}`, opts(ctx));
  return r.data;
}

export async function voidLabStatement(ctx: Ctx, labId: string, statementId: string) {
  await apiRequest(`${BASE}/${encodeURIComponent(labId)}/statements/${encodeURIComponent(statementId)}/void`, opts(ctx, { method: "POST", body: {} }));
}

export async function addLabPayment(
  ctx: Ctx,
  labId: string,
  body: { amount: number; paid_at: string; method?: string; reference?: string; note?: string },
) {
  await apiRequest(`${BASE}/${encodeURIComponent(labId)}/payments`, opts(ctx, { method: "POST", body }));
}
