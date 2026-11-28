import { API_BASE_URL } from "@/lib/constants";
import { authHeaders, downloadFile, failFrom } from "@/lib/api/clinicBilling";
import { apiRequest } from "@/services/api";

type Ctx = { token: string; organizationId?: string | null };
const BASE = "/api/v1/reception/workspace/crm";

function opts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return { token: ctx.token, organizationId: ctx.organizationId ?? null, timeoutMs: 30_000, ...extra };
}

export const STAGES = ["LEAD", "MET", "QUOTED", "CONTRACTED", "ACTIVE", "LOST"] as const;
export type Stage = (typeof STAGES)[number];
export const STAGE_LABELS: Record<Stage, string> = {
  LEAD: "Tiềm năng",
  MET: "Đã gặp",
  QUOTED: "Đã báo giá",
  CONTRACTED: "Đã ký hợp đồng",
  ACTIVE: "Đang gửi mẫu",
  LOST: "Ngừng / mất",
};
export const KIND_LABELS: Record<string, string> = { CALL: "Gọi điện", VISIT: "Gặp trực tiếp", MESSAGE: "Nhắn tin", NOTE: "Ghi chú" };
export const TYPE_LABELS: Record<string, string> = { CLINIC: "Phòng khám", HOSPITAL: "Bệnh viện", OTHER: "Khác" };

export type CrmAccount = {
  id: string;
  name: string;
  account_type: string;
  organization_id: string | null;
  stage: Stage;
  owner_user_id: string | null;
  owner_name: string | null;
  contact_person: string | null;
  phone: string | null;
  address: string | null;
  district: string | null;
  est_monthly_cases: number;
  next_followup_date: string | null;
  followup_overdue: boolean;
  notes: string | null;
  cases: number;
  revenue: number;
  margin?: number;
  share_pct: number | null;
  days_quiet: number | null;
  last_activity_at: string | null;
};

export type CrmList = {
  month: string;
  is_admin: boolean;
  stage_counts: Record<string, number>;
  totals: {
    accounts: number;
    est_monthly_cases: number;
    cases: number;
    share_pct: number | null;
    revenue: number;
    margin?: number;
    overdue_followups: number;
    quiet_accounts: number;
  };
  accounts: CrmAccount[];
};

export type CrmDetail = {
  account: CrmAccount;
  history: { month: string; cases: number; revenue: number }[];
  activities: { id: string; kind: string; summary: string; by: string | null; at: string | null }[];
};

export type SaleRow = {
  user_id: string;
  email: string;
  accounts: number;
  active_accounts: number;
  cases: number;
  revenue: number;
  margin: number;
  target_cases: number;
  target_revenue: number;
  cases_pct: number | null;
  revenue_pct: number | null;
};

export async function listAccounts(ctx: Ctx, month: string, stage: string, q: string) {
  const qs = new URLSearchParams();
  if (month) qs.set("month", month);
  if (stage) qs.set("stage", stage);
  if (q) qs.set("q", q);
  const r = await apiRequest<{ data: CrmList }>(`${BASE}/accounts?${qs.toString()}`, opts(ctx));
  return r.data;
}

export async function createAccount(ctx: Ctx, body: Record<string, unknown>) {
  await apiRequest(`${BASE}/accounts`, opts(ctx, { method: "POST", body }));
}

export async function updateAccount(ctx: Ctx, id: string, body: Record<string, unknown>) {
  await apiRequest(`${BASE}/accounts/${encodeURIComponent(id)}`, opts(ctx, { method: "POST", body }));
}

export async function getAccount(ctx: Ctx, id: string) {
  const r = await apiRequest<{ data: CrmDetail }>(`${BASE}/accounts/${encodeURIComponent(id)}`, opts(ctx));
  return r.data;
}

export async function addActivity(ctx: Ctx, id: string, body: { kind: string; summary: string; next_followup_date?: string }) {
  await apiRequest(`${BASE}/accounts/${encodeURIComponent(id)}/activities`, opts(ctx, { method: "POST", body }));
}

export async function listSales(ctx: Ctx, month: string) {
  const r = await apiRequest<{ data: { month: string; sales: SaleRow[] } }>(`${BASE}/sales?month=${encodeURIComponent(month)}`, opts(ctx));
  return r.data;
}

export async function setSaleTarget(ctx: Ctx, userId: string, body: { month: string; target_cases: number; target_revenue: number }) {
  await apiRequest(`${BASE}/sales/${encodeURIComponent(userId)}/target`, opts(ctx, { method: "POST", body }));
}

export type ImportResult = {
  applied: boolean;
  created: number;
  skipped_count: number;
  skipped: { row: number; name: string; reason: string }[];
  error_count: number;
  errors: { row: number; error: string }[];
};

export async function downloadAccountsExcel(ctx: Ctx, month: string) {
  await downloadFile(ctx, `${BASE}/accounts/export?month=${encodeURIComponent(month)}`, "khach-hang.xlsx");
}

export async function downloadImportTemplate(ctx: Ctx) {
  await downloadFile(ctx, `${BASE}/accounts/import/template`, "mau-nhap-khach-hang.xlsx");
}

export async function importAccounts(ctx: Ctx, file: File, apply: boolean): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("apply", apply ? "1" : "0");
  const res = await fetch(`${API_BASE_URL}${BASE}/accounts/import`, { method: "POST", headers: authHeaders(ctx), body: form });
  if (!res.ok) await failFrom(res);
  return ((await res.json()) as { data: ImportResult }).data;
}

export type DistrictShare = {
  district: string;
  accounts: number;
  active_accounts: number;
  linked_accounts: number;
  est_monthly_cases: number;
  cases: number;
  share_pct: number | null;
  revenue: number;
  margin?: number;
};

export async function getMarket(ctx: Ctx, month: string) {
  const r = await apiRequest<{ data: { districts: DistrictShare[] } }>(`${BASE}/market?month=${encodeURIComponent(month)}`, opts(ctx));
  return r.data.districts;
}
