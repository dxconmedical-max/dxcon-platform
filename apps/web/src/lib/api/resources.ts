import { apiRequest, type ApiEnvelope } from "./client";

export type PatientRow = {
  id?: string;
  patient_code?: string;
  full_name?: string;
  phone?: string;
  email?: string;
  gender?: string;
};

export type OrderRow = {
  id?: string;
  order_code?: string;
  patient_id?: string;
  status?: string;
  total_amount?: number;
};

export type PaginatedResult<T> = {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
};

export async function fetchPatients(
  token: string,
  organizationId: string,
): Promise<PaginatedResult<PatientRow>> {
  const response = await apiRequest<{ count: number; patients: PatientRow[] }>(
    "/api/v1/patients",
    { token, organizationId },
  );
  return {
    items: response.patients ?? [],
    total: response.count ?? 0,
    page: 1,
    pageSize: response.count ?? 0,
  };
}

export async function fetchOrders(
  token: string,
  organizationId: string,
): Promise<PaginatedResult<OrderRow>> {
  const response = await apiRequest<{ count: number; orders: OrderRow[] }>(
    "/api/v1/orders",
    { token, organizationId },
  );
  return {
    items: response.orders ?? [],
    total: response.count ?? 0,
    page: 1,
    pageSize: response.count ?? 0,
  };
}

export async function searchDoctorPatients(
  token: string,
  organizationId: string,
  query?: string,
  page = 1,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const params = new URLSearchParams({ page: String(page), per_page: "25" });
  if (query) params.set("q", query);
  const response = await apiRequest<{
    success?: boolean;
    data?: Record<string, unknown>[];
    total?: number;
    page?: number;
    per_page?: number;
  }>(`/api/v1/portal/doctor/patients/search?${params}`, {
    token,
    organizationId,
  });
  const items = Array.isArray(response.data) ? response.data : [];
  return {
    items,
    total: response.total ?? items.length,
    page: response.page ?? page,
    pageSize: response.per_page ?? 25,
  };
}

export async function fetchClinicPatients(
  token: string,
  organizationId: string,
  clinicId?: string,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const query = clinicId ? `?clinic_id=${encodeURIComponent(clinicId)}` : "";
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>[]> | Record<string, unknown>>(
    `/api/v1/clinic/patients${query}`,
    { token, organizationId },
  );
  const items = Array.isArray((response as ApiEnvelope<Record<string, unknown>[]>).data)
    ? (response as ApiEnvelope<Record<string, unknown>[]>).data
    : Array.isArray((response as { patients?: unknown }).patients)
      ? ((response as { patients: Record<string, unknown>[] }).patients)
      : [];
  return { items, total: items.length, page: 1, pageSize: items.length || 25 };
}

export async function fetchClinicOrders(
  token: string,
  organizationId: string,
  clinicId?: string,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const query = clinicId ? `?clinic_id=${encodeURIComponent(clinicId)}` : "";
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>[]> | Record<string, unknown>>(
    `/api/v1/clinic/orders${query}`,
    { token, organizationId },
  );
  const items = Array.isArray((response as ApiEnvelope<Record<string, unknown>[]>).data)
    ? (response as ApiEnvelope<Record<string, unknown>[]>).data
    : Array.isArray((response as { orders?: unknown }).orders)
      ? ((response as { orders: Record<string, unknown>[] }).orders)
      : [];
  return { items, total: items.length, page: 1, pageSize: items.length || 25 };
}

export async function fetchLabTestingQueue(
  token: string,
  organizationId: string,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    "/api/v1/lab/workspace/testing-queue",
    { token, organizationId },
  );
  const queue = (response.data?.queue ?? response.data?.items ?? []) as Record<string, unknown>[];
  const items = Array.isArray(queue) ? queue : [];
  return { items, total: items.length, page: 1, pageSize: items.length || 25 };
}

export async function fetchPatientHistory(
  token: string,
  organizationId: string,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    "/api/v1/portal/patient/history",
    { token, organizationId },
  );
  const events = (response.data?.events ?? response.data?.orders ?? []) as Record<string, unknown>[];
  const items = Array.isArray(events) ? events : [];
  return { items, total: items.length, page: 1, pageSize: items.length || 25 };
}

export async function fetchPatientReleasedReports(
  token: string,
  organizationId: string,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    "/api/v1/portal/patient/dashboard",
    { token, organizationId },
  );
  const reports = (response.data?.released_reports ?? []) as Record<string, unknown>[];
  const items = Array.isArray(reports) ? reports : [];
  return { items, total: items.length, page: 1, pageSize: items.length || 25 };
}

export async function fetchDoctorPendingReviews(
  token: string,
  organizationId: string,
): Promise<PaginatedResult<Record<string, unknown>>> {
  const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
    "/api/v1/portal/doctor/dashboard",
    { token, organizationId },
  );
  const reviews = (response.data?.pending_reviews ?? []) as Record<string, unknown>[];
  const items = Array.isArray(reviews) ? reviews : [];
  return { items, total: items.length, page: 1, pageSize: items.length || 25 };
}
