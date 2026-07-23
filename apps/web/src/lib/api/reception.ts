import { apiRequest } from "@/services/api";
import { ApiError } from "@/lib/errors";

export type ReceptionPatient = {
  patient_code: string;
  full_name: string;
  phone?: string | null;
  national_id?: string | null;
  email?: string | null;
  address?: string | null;
  gender?: string | null;
  date_of_birth?: string | null;
  qr_payload?: string;
};

export type WalkInRegistration = {
  full_name: string;
  phone: string;
  date_of_birth?: string;
  gender?: string;
  email?: string;
  address?: string;
  national_id?: string;
  note?: string;
  force?: boolean;
};

export type DuplicateWarning = {
  patient_code?: string;
  full_name?: string;
  phone?: string;
  national_id?: string;
  reason?: string;
  [key: string]: unknown;
};

export type ReceptionTest = {
  id: string;
  code: string;
  name: string;
  category?: string | null;
  sample_type?: string | null;
  price?: number | null;
};

export type ReceptionOrderPricing = {
  subtotal: number;
  discount: number;
  total: number;
};

export type ReceptionOrderCreate = {
  order: Record<string, unknown>;
  invoice: Record<string, unknown>;
  pricing: ReceptionOrderPricing;
};

export type ReceptionPaymentResult = {
  payment: Record<string, unknown>;
  invoice: Record<string, unknown> | null;
  order_status: string | null;
  barcodes: ReceptionBarcodes;
};

export type ReceptionBarcodes = {
  order_barcode?: string;
  patient_barcode?: string;
  patient_qr?: string;
  collection_barcode?: string | null;
  sample_barcodes?: Array<{
    test_code: string;
    test_name: string;
    barcode: string;
  }>;
};

type Ctx = { token: string; organizationId?: string | null };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

function listRowsFromEnvelope(body: Record<string, unknown>): Record<string, unknown>[] {
  if (Array.isArray(body.data)) return body.data as Record<string, unknown>[];
  const nested = body.data;
  if (nested && typeof nested === "object" && Array.isArray((nested as Record<string, unknown>).data)) {
    return (nested as Record<string, unknown>).data as Record<string, unknown>[];
  }
  return [];
}

function paginationTotal(body: Record<string, unknown>, fallback: number): number {
  const top = body.pagination as { total?: number } | undefined;
  if (top?.total != null) return top.total;
  const nested = body.data;
  if (nested && typeof nested === "object") {
    const nestedPagination = (nested as Record<string, unknown>).pagination as
      | { total?: number }
      | undefined;
    if (nestedPagination?.total != null) return nestedPagination.total;
  }
  return fallback;
}

function mapPatient(row: Record<string, unknown>): ReceptionPatient {
  return {
    patient_code: String(row.patient_code ?? row.id ?? "—"),
    full_name: String(row.full_name ?? "—"),
    phone: row.phone != null ? String(row.phone) : null,
    national_id: row.national_id != null ? String(row.national_id) : null,
    email: row.email != null ? String(row.email) : null,
    address: row.address != null ? String(row.address) : null,
    gender: row.gender != null ? String(row.gender) : null,
    date_of_birth: row.date_of_birth != null ? String(row.date_of_birth) : null,
    qr_payload: row.qr_payload != null ? String(row.qr_payload) : undefined,
  };
}

/** GET /api/v1/reception/workspace/search */
export async function searchReceptionPatients(
  { token, organizationId }: Ctx,
  query: string,
): Promise<{ items: ReceptionPatient[]; total: number }> {
  const params = new URLSearchParams({ q: query, limit: "25" });
  const response = await apiRequest<Record<string, unknown>>(
    `/api/v1/reception/workspace/search?${params}`,
    { token, organizationId },
  );
  const raw = listRowsFromEnvelope(response);
  return {
    items: raw.map(mapPatient),
    total: paginationTotal(response, raw.length),
  };
}

/**
 * POST /api/v1/reception/workspace/patients/register
 * Throws ApiError 409 with details.warnings when duplicates exist and force is false.
 */
export async function registerWalkIn(
  { token, organizationId }: Ctx,
  registration: WalkInRegistration,
): Promise<{
  patient_code: string;
  message: string;
  patient: ReceptionPatient;
  qr_payload?: string;
  warnings: DuplicateWarning[];
}> {
  try {
    const response = await apiRequest<{
      success: boolean;
      data: Record<string, unknown>;
    }>("/api/v1/reception/workspace/patients/register", {
      token,
      organizationId,
      method: "POST",
      body: registration,
    });
    const data = response.data ?? {};
    const patientRow =
      data.patient && typeof data.patient === "object"
        ? (data.patient as Record<string, unknown>)
        : data;
    const code = patientRow.patient_code ?? data.patient_code;
    if (!code) {
      throw new ApiError("Patient registration did not return a patient code", 502, {
        code: "MISSING_PATIENT_CODE",
      });
    }
    const patient = mapPatient({
      ...patientRow,
      patient_code: code,
      full_name: patientRow.full_name ?? registration.full_name,
      phone: patientRow.phone ?? registration.phone,
    });
    return {
      patient_code: String(code),
      message: String(data.message ?? "Patient registered."),
      patient,
      qr_payload:
        data.qr_payload != null
          ? String(data.qr_payload)
          : patient.qr_payload,
      warnings: asArray(data.warnings) as DuplicateWarning[],
    };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const body =
        error.body && typeof error.body === "object"
          ? (error.body as Record<string, unknown>)
          : {};
      throw new ApiError("Possible duplicate patient found", 409, {
        ...body,
        duplicate: true,
        warnings: asArray(body.warnings),
      });
    }
    throw error;
  }
}

/** GET /api/v1/reception/workspace/tests */
export async function fetchReceptionTests(
  { token, organizationId }: Ctx,
  params: { q?: string; category?: string; limit?: number } = {},
): Promise<{ items: ReceptionTest[]; total: number }> {
  const qs = new URLSearchParams();
  qs.set("limit", String(params.limit ?? 100));
  qs.set("page", "1");
  if (params.q) qs.set("q", params.q);
  if (params.category) qs.set("category", params.category);

  const response = await apiRequest<Record<string, unknown>>(
    `/api/v1/reception/workspace/tests?${qs}`,
    { token, organizationId },
  );
  const raw = listRowsFromEnvelope(response);
  return {
    items: raw.map((t) => ({
      id: String(t.id),
      code: String(t.code),
      name: String(t.name),
      category: t.category != null ? String(t.category) : null,
      sample_type: t.sample_type != null ? String(t.sample_type) : null,
      price: t.price != null ? Number(t.price) : null,
    })),
    total: paginationTotal(response, raw.length),
  };
}

/** POST /api/v1/reception/workspace/orders */
export async function createReceptionOrder(
  { token, organizationId }: Ctx,
  payload: {
    patient_code: string;
    test_catalog_ids: string[];
    discount?: number;
    note?: string;
    queue_entry_id?: string;
  },
): Promise<ReceptionOrderCreate> {
  const response = await apiRequest<{ success: boolean; data: ReceptionOrderCreate }>(
    "/api/v1/reception/workspace/orders",
    {
      token,
      organizationId,
      method: "POST",
      body: {
        patient_code: payload.patient_code,
        test_catalog_ids: payload.test_catalog_ids,
        discount: payload.discount ?? 0,
        note: payload.note,
        queue_entry_id: payload.queue_entry_id,
      },
    },
  );
  return response.data;
}

/** POST /api/v1/reception/workspace/orders/:ref/payment */
export async function collectReceptionPayment(
  { token, organizationId }: Ctx,
  orderRef: string,
  payload: { payment_method?: string; receipt_number?: string } = {},
): Promise<ReceptionPaymentResult> {
  const response = await apiRequest<{ success: boolean; data: ReceptionPaymentResult }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/payment`,
    {
      token,
      organizationId,
      method: "POST",
      body: {
        payment_method: payload.payment_method ?? "cash",
        receipt_number: payload.receipt_number,
      },
    },
  );
  return response.data;
}

/** GET /api/v1/reception/workspace/orders/:ref/barcode */
export async function fetchReceptionBarcodes(
  { token, organizationId }: Ctx,
  orderRef: string,
): Promise<ReceptionBarcodes> {
  const response = await apiRequest<{ success: boolean; data: ReceptionBarcodes }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/barcode`,
    { token, organizationId },
  );
  return response.data;
}

/** GET /api/v1/reception/workspace/orders/:ref/request-form */
export async function fetchReceptionRequestForm(
  { token, organizationId }: Ctx,
  orderRef: string,
): Promise<{ html: string }> {
  const response = await apiRequest<{ success: boolean; data: { html: string } }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/request-form`,
    { token, organizationId },
  );
  return response.data;
}

export function getOrderCode(
  order: ReceptionOrderCreate["order"] | null | undefined,
): string {
  if (!order) return "";
  const row = order as Record<string, unknown>;
  const code = row.order_code ?? row.orderRef ?? row.id;
  return code ? String(code) : "";
}

export function getDuplicateWarnings(error: unknown): DuplicateWarning[] {
  if (!(error instanceof ApiError) || error.status !== 409) return [];
  const body =
    error.body && typeof error.body === "object"
      ? (error.body as Record<string, unknown>)
      : {};
  return Array.isArray(body.warnings) ? (body.warnings as DuplicateWarning[]) : [];
}
