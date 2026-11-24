import { apiRequest } from "@/services/api";

export type DemoRequestBody = {
  full_name: string;
  organization?: string;
  email: string;
  phone?: string;
  message?: string;
  lang: "vi" | "en";
  consent_contact: boolean;
  /** Honeypot — must stay empty for real people. */
  website?: string;
};

/** Anonymous POST from the landing page "Book a demo" form. */
export async function submitDemoRequest(body: DemoRequestBody): Promise<{ reference: string }> {
  const response = await apiRequest<{ success: boolean; data: { reference: string } }>(
    "/api/v1/public/demo-requests",
    { method: "POST", body, timeoutMs: 30_000 },
  );
  return response.data;
}

export const DEMO_STATUSES = ["NEW", "CONTACTED", "DONE", "SPAM"] as const;
export type DemoStatus = (typeof DEMO_STATUSES)[number];

export type DemoRequestItem = {
  id: string;
  reference: string;
  full_name: string;
  organization: string | null;
  email: string;
  phone: string | null;
  message: string | null;
  lang: string | null;
  status: DemoStatus;
  handled_by: string | null;
  handled_at: string | null;
  created_at: string | null;
};

type Ctx = { token: string; organizationId?: string | null };

export async function listDemoRequests(
  ctx: Ctx,
  status?: DemoStatus,
): Promise<{ items: DemoRequestItem[]; new_count: number }> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await apiRequest<{
    success: boolean;
    data: { items: DemoRequestItem[]; new_count: number };
  }>(`/api/v1/reception/workspace/demo-requests${query}`, {
    token: ctx.token,
    organizationId: ctx.organizationId ?? null,
    timeoutMs: 30_000,
  });
  return response.data;
}

export async function setDemoStatus(ctx: Ctx, id: string, status: DemoStatus): Promise<DemoRequestItem> {
  const response = await apiRequest<{ success: boolean; data: DemoRequestItem }>(
    `/api/v1/reception/workspace/demo-requests/${encodeURIComponent(id)}/status`,
    {
      method: "POST",
      token: ctx.token,
      organizationId: ctx.organizationId ?? null,
      body: { status },
      timeoutMs: 30_000,
    },
  );
  return response.data;
}
