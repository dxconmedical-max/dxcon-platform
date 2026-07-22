/**
 * Live diagnostic order workflow API — no sample/mock fallbacks.
 * Paths must match backend/app/api/diagnostic_workflow/routes.py.
 */

import { apiRequest } from "./client";

export type WorkflowCtx = { token: string; organizationId: string };

export type CatalogTest = {
  id?: string;
  code?: string;
  name?: string;
  category?: string;
  sample_type?: string;
  price?: number;
};

export type WorkflowPatient = {
  patient_code: string;
  full_name: string;
  phone?: string | null;
  email?: string | null;
  gender?: string | null;
};

export type WorkflowOrder = {
  order_code: string;
  patient_code?: string;
  patient_name?: string;
  status: string;
  milestone?: string;
  total_amount?: number;
  barcode_value?: string | null;
  items?: Array<{
    test_code?: string;
    test_name?: string;
    unit_price?: number;
    line_total?: number;
  }>;
  collection?: Record<string, unknown> | null;
  result?: {
    result_code?: string;
    status?: string;
    html_content?: string | null;
  } | null;
  timeline?: Array<{ label?: string; status?: string; time?: string }>;
};

type Envelope<T> = { success: boolean; data: T; error?: string; message?: string; code?: string };

async function call<T>(
  path: string,
  ctx: WorkflowCtx,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  const response = await apiRequest<Envelope<T>>(path, {
    token: ctx.token,
    organizationId: ctx.organizationId,
    method: options.method,
    body: options.body,
  });
  if (!response.success || response.data === undefined) {
    throw new Error(response.error || response.message || "Workflow request failed");
  }
  return response.data;
}

export async function fetchCatalog(ctx: WorkflowCtx): Promise<CatalogTest[]> {
  const data = await call<{ items: CatalogTest[] }>("/api/v1/diagnostic-workflow/catalog", ctx);
  return data.items ?? [];
}

export async function searchPatients(ctx: WorkflowCtx, query: string): Promise<WorkflowPatient[]> {
  const params = new URLSearchParams({ q: query, limit: "25" });
  const data = await call<{ items: WorkflowPatient[] }>(
    `/api/v1/diagnostic-workflow/patients?${params}`,
    ctx,
  );
  return data.items ?? [];
}

export async function createPatient(
  ctx: WorkflowCtx,
  payload: {
    full_name: string;
    phone?: string;
    email?: string;
    gender?: string;
    date_of_birth?: string;
  },
): Promise<WorkflowPatient> {
  return call<WorkflowPatient>("/api/v1/diagnostic-workflow/patients", ctx, {
    method: "POST",
    body: payload,
  });
}

export async function createOrder(
  ctx: WorkflowCtx,
  payload: { patient_code: string; test_catalog_ids: string[]; note?: string },
): Promise<WorkflowOrder> {
  return call<WorkflowOrder>("/api/v1/diagnostic-workflow/orders", ctx, {
    method: "POST",
    body: payload,
  });
}

export async function getOrder(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}`,
    ctx,
  );
}

export async function payOrder(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/pay`,
    ctx,
    { method: "POST", body: { payment_method: "cash" } },
  );
}

export async function scheduleCollection(
  ctx: WorkflowCtx,
  orderRef: string,
): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/collection`,
    ctx,
    {
      method: "POST",
      body: { collector_name: "On-site Collector", pickup_address: "Reception Desk" },
    },
  );
}

export async function collectSample(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/collect`,
    ctx,
    { method: "POST", body: {} },
  );
}

export async function markInTransit(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/transit`,
    ctx,
    { method: "POST", body: {} },
  );
}

export async function receiveAtLab(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/receive`,
    ctx,
    { method: "POST", body: { received_by: "Lab tech" } },
  );
}

export async function enterResults(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/results`,
    ctx,
    { method: "POST", body: {} },
  );
}

export async function completeQc(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/qc`,
    ctx,
    { method: "POST", body: {} },
  );
}

export async function approveResult(
  ctx: WorkflowCtx,
  orderRef: string,
  doctorNote = "Approved",
): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/approve`,
    ctx,
    { method: "POST", body: { doctor_note: doctorNote } },
  );
}

export async function releaseResult(ctx: WorkflowCtx, orderRef: string): Promise<WorkflowOrder> {
  return call<WorkflowOrder>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/release`,
    ctx,
    { method: "POST", body: {} },
  );
}

export async function fetchReport(
  ctx: WorkflowCtx,
  orderRef: string,
): Promise<{ html: string; filename: string; result_code?: string }> {
  return call<{ html: string; filename: string; result_code?: string }>(
    `/api/v1/diagnostic-workflow/orders/${encodeURIComponent(orderRef)}/report`,
    ctx,
  );
}

export function downloadHtmlReport(html: string, filename: string) {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename.endsWith(".html") ? filename : `${filename}.html`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
