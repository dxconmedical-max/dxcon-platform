import { apiRequest } from "@/services/api";

type Ctx = { token: string; organizationId?: string | null };

export type SlipStatus = "NEW" | "APPROVED" | "REJECTED";

export type SlipTest = { id: string; code: string; name: string };

export type ClinicSlip = {
  id: string;
  reference: string;
  organization_id: string;
  organization_name: string | null;
  requested_by: string | null;
  patient_name: string;
  birth_year: number;
  birth_date: string | null;
  tests: SlipTest[];
  tube_count: number;
  status: SlipStatus;
  order_code: string | null;
  reject_reason: string | null;
  handled_by: string | null;
  created_at: string | null;
};

export type CatalogTest = { id: string; code: string; name: string; sample_type: string | null };

export type SlipBody = { patient_name: string; birth_year: number; birth_date?: string; tube_count: number; test_ids: string[] };

function opts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000, ...extra };
}

export async function getClinicOrderStatus(ctx: Ctx): Promise<{ enabled: boolean; can_submit: boolean }> {
  const r = await apiRequest<{ data: { enabled: boolean; can_submit: boolean } }>("/api/v1/clinic-orders/status", opts(ctx));
  return r.data;
}

export async function searchClinicTests(ctx: Ctx, q: string): Promise<CatalogTest[]> {
  const r = await apiRequest<{ data: CatalogTest[] }>(`/api/v1/clinic-orders/tests?q=${encodeURIComponent(q)}`, opts(ctx));
  return r.data ?? [];
}

export async function submitClinicSlip(ctx: Ctx, body: SlipBody): Promise<ClinicSlip> {
  const r = await apiRequest<{ data: ClinicSlip }>("/api/v1/clinic-orders/requests", opts(ctx, { method: "POST", body }));
  return r.data;
}

export async function listClinicSlips(ctx: Ctx): Promise<ClinicSlip[]> {
  const r = await apiRequest<{ data: ClinicSlip[] }>("/api/v1/clinic-orders/requests", opts(ctx));
  return r.data ?? [];
}

// ---- DxCon staff side
export async function listStaffSlips(ctx: Ctx, status?: SlipStatus): Promise<{ items: ClinicSlip[]; new_count: number }> {
  const q = status ? `?status=${status}` : "";
  const r = await apiRequest<{ data: { items: ClinicSlip[]; new_count: number } }>(
    `/api/v1/reception/workspace/clinic-requests${q}`,
    opts(ctx),
  );
  return r.data;
}

export async function approveSlip(ctx: Ctx, id: string): Promise<ClinicSlip> {
  const r = await apiRequest<{ data: ClinicSlip }>(
    `/api/v1/reception/workspace/clinic-requests/${encodeURIComponent(id)}/approve`,
    opts(ctx, { method: "POST", body: {} }),
  );
  return r.data;
}

export async function rejectSlip(ctx: Ctx, id: string, reason: string): Promise<ClinicSlip> {
  const r = await apiRequest<{ data: ClinicSlip }>(
    `/api/v1/reception/workspace/clinic-requests/${encodeURIComponent(id)}/reject`,
    opts(ctx, { method: "POST", body: { reason } }),
  );
  return r.data;
}

export type ClinicSetting = { id: string; code: string; name: string; enabled: boolean };

export async function listClinicSettings(ctx: Ctx): Promise<ClinicSetting[]> {
  const r = await apiRequest<{ data: ClinicSetting[] }>("/api/v1/reception/workspace/clinic-order-settings", opts(ctx));
  return r.data ?? [];
}

export async function setClinicSetting(ctx: Ctx, id: string, enabled: boolean): Promise<void> {
  await apiRequest(`/api/v1/reception/workspace/clinic-order-settings/${encodeURIComponent(id)}`, opts(ctx, { method: "POST", body: { enabled } }));
}
