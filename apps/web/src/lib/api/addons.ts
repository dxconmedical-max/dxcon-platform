import { apiRequest } from "@/services/api";

type Ctx = { token: string; organizationId?: string | null };
const BASE = "/api/v1/reception/workspace";

function opts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000, ...extra };
}

export type AddonCandidate = {
  order_code: string;
  patient_name: string;
  patient_code: string;
  status: string;
  collected_at: string;
  hours_since_collected: number;
  tests: string[];
};

export type AddonTest = {
  id: string;
  code: string;
  name: string;
  sample_type: string | null;
  price: number;
  window_hours: number;
  hours_left: number;
  allowed: boolean;
  already_in_order: boolean;
  is_sendout: boolean;
  sendout_eta_days: number | null;
};

export type SendoutStatus = "OVERDUE" | "DUE_SOON" | "WAITING";

export type SendoutItem = {
  order_code: string;
  patient_name: string;
  test_code: string;
  test_name: string;
  destination: string | null;
  collected_at: string;
  sent_at: string | null;
  eta_date: string;
  days_left: number;
  status: SendoutStatus;
  note: string | null;
};

export type TestFlagRow = {
  id: string;
  code: string;
  name: string;
  is_sendout: boolean;
  sendout_destination: string | null;
  sendout_eta_days: number | null;
  addon_window_hours: number | null;
};

export async function findAddonCandidates(ctx: Ctx, q: string): Promise<AddonCandidate[]> {
  const r = await apiRequest<{ data: AddonCandidate[] }>(`${BASE}/addons/candidates?q=${encodeURIComponent(q)}`, opts(ctx));
  return r.data ?? [];
}

export async function listAddonTests(ctx: Ctx, orderCode: string, q: string): Promise<AddonTest[]> {
  const r = await apiRequest<{ data: AddonTest[] }>(
    `${BASE}/addons/tests?order_code=${encodeURIComponent(orderCode)}&q=${encodeURIComponent(q)}`,
    opts(ctx),
  );
  return r.data ?? [];
}

export async function createAddon(ctx: Ctx, orderCode: string, testIds: string[]): Promise<{ addon_order_code: string }> {
  const r = await apiRequest<{ data: { addon_order_code: string } }>(
    `${BASE}/orders/${encodeURIComponent(orderCode)}/addons`,
    opts(ctx, { method: "POST", body: { test_catalog_ids: testIds } }),
  );
  return r.data;
}

export async function listSendout(ctx: Ctx): Promise<{ items: SendoutItem[]; counts: { overdue: number; due_soon: number; total: number } }> {
  const r = await apiRequest<{ data: { items: SendoutItem[]; counts: { overdue: number; due_soon: number; total: number } } }>(
    `${BASE}/sendout-reminders`,
    opts(ctx),
  );
  return r.data;
}

export async function updateSendout(
  ctx: Ctx,
  orderCode: string,
  testCode: string,
  body: { sent_at?: string; eta_date?: string; destination?: string; note?: string; dismissed?: boolean },
): Promise<void> {
  await apiRequest(`${BASE}/sendout-reminders/${encodeURIComponent(orderCode)}/${encodeURIComponent(testCode)}`, opts(ctx, { method: "POST", body }));
}

export async function listTestFlags(ctx: Ctx, q: string): Promise<TestFlagRow[]> {
  const r = await apiRequest<{ data: TestFlagRow[] }>(`${BASE}/test-flags?q=${encodeURIComponent(q)}`, opts(ctx));
  return r.data ?? [];
}

export async function saveTestFlag(
  ctx: Ctx,
  id: string,
  body: { is_sendout: boolean; sendout_destination?: string; sendout_eta_days?: number | null; addon_window_hours?: number | null },
): Promise<void> {
  await apiRequest(`${BASE}/test-flags/${encodeURIComponent(id)}`, opts(ctx, { method: "POST", body }));
}
