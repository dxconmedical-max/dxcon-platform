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
  patient_code?: string;
  note?: string;
  force?: boolean;
};

export type DuplicateWarning = {
  patient_code?: string;
  full_name?: string;
  phone?: string;
  national_id?: string;
  field?: string;
  message?: string;
  reason?: string;
  [key: string]: unknown;
};

export type ReceptionTest = {
  id: string;
  code: string;
  name: string;
  category?: string | null;
  sample_type?: string | null;
  turnaround_hours?: number | null;
  price?: number | null;
};

export type ReceptionOrderPricing = {
  subtotal: number;
  discount: number;
  total: number;
  tax?: number | null;
};

export type ReceptionOrderCreate = {
  order: Record<string, unknown>;
  invoice: Record<string, unknown>;
  pricing: ReceptionOrderPricing;
};

export type ReceptionOrderDetail = {
  order: Record<string, unknown>;
  pricing: ReceptionOrderPricing;
  payment_summary?: ReceptionPaymentSummary | null;
  payment?: ReceptionPaymentRecord | null;
  invoice?: Record<string, unknown> | null;
};

export type ReceptionPaymentSummary = {
  order_total: number;
  paid_amount: number;
  outstanding_amount: number;
  discount?: number;
  subtotal?: number;
  tax?: number | null;
  status: string;
  payment_methods_supported?: string[];
  partial_payments_supported?: boolean;
};

export type ReceptionPaymentRecord = {
  id?: string;
  receipt_number: string;
  payment_method: string;
  amount: number;
  paid_at?: string | null;
  created_by?: string | null;
};

export type ReceptionPaymentResult = {
  payment: ReceptionPaymentRecord | null;
  invoice: Record<string, unknown> | null;
  order_status: string | null;
  payment_summary: ReceptionPaymentSummary;
  idempotent_replay?: boolean;
};

export type ReceptionSampleBarcode = {
  test_code: string;
  test_name: string;
  sample_type?: string;
  specimen_code?: string;
  barcode: string;
  collection_requirement?: string;
};

export type ReceptionBarcodes = {
  order_code?: string;
  patient_code?: string;
  patient_name?: string | null;
  order_barcode: string;
  patient_barcode: string;
  patient_qr: string;
  sample_barcodes: ReceptionSampleBarcode[];
  collection_barcode?: string | null;
  generated_at?: string;
  reprint?: boolean;
  status?: string;
};

export type ReceptionRequestForm = {
  html: string;
  order_code?: string;
  patient_code?: string;
  barcodes?: ReceptionBarcodes;
  reprint?: boolean;
  generated_at?: string;
};

export const RECEPTION_PAYMENT_METHODS = [
  "cash",
  "transfer",
  "qr",
  "pos",
  "corporate",
  "insurance",
] as const;

export const RECEPTION_PAYMENT_TIMEOUT_MS = 30_000;

export const PATIENT_QR_PREFIX = "dxcon:patient:";

type Ctx = {
  token: string;
  organizationId?: string | null;
  signal?: AbortSignal;
  timeoutMs?: number;
};

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

function mapPricing(raw: Record<string, unknown> | undefined): ReceptionOrderPricing {
  const source = raw ?? {};
  return {
    subtotal: Number(source.subtotal ?? 0),
    discount: Number(source.discount ?? 0),
    total: Number(source.total ?? source.total_amount ?? 0),
    tax: source.tax != null ? Number(source.tax) : null,
  };
}

function requestOpts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return {
    token: ctx.token,
    organizationId: ctx.organizationId,
    signal: ctx.signal,
    timeoutMs: ctx.timeoutMs,
    ...extra,
  };
}

/** GET /api/v1/reception/workspace/search */
export async function searchReceptionPatients(
  ctx: Ctx,
  query: string,
): Promise<{ items: ReceptionPatient[]; total: number }> {
  const params = new URLSearchParams({ q: query, limit: "25" });
  const response = await apiRequest<Record<string, unknown>>(
    `/api/v1/reception/workspace/search?${params}`,
    requestOpts(ctx),
  );
  const raw = listRowsFromEnvelope(response);
  return {
    items: raw.map(mapPatient),
    total: paginationTotal(response, raw.length),
  };
}

/**
 * POST /api/v1/reception/workspace/patients/register
 * 409 → ApiError with duplicate warnings when force is false.
 */
export async function registerWalkIn(
  ctx: Ctx,
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
      ...requestOpts(ctx, { method: "POST", body: registration }),
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
        data.qr_payload != null ? String(data.qr_payload) : patient.qr_payload,
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

/** GET /api/v1/reception/workspace/patients/:code — confirm persistence */
export async function fetchReceptionPatient(
  ctx: Ctx,
  patientCode: string,
): Promise<ReceptionPatient & { orders?: Record<string, unknown>[] }> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/patients/${encodeURIComponent(patientCode)}`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    ...mapPatient(data),
    orders: asArray(data.orders),
  };
}

/** GET /api/v1/reception/workspace/tests */
export async function fetchReceptionTests(
  ctx: Ctx,
  params: { q?: string; category?: string; limit?: number } = {},
): Promise<{ items: ReceptionTest[]; total: number }> {
  const qs = new URLSearchParams();
  qs.set("limit", String(params.limit ?? 100));
  qs.set("page", "1");
  if (params.q) qs.set("q", params.q);
  if (params.category) qs.set("category", params.category);

  const response = await apiRequest<Record<string, unknown>>(
    `/api/v1/reception/workspace/tests?${qs}`,
    requestOpts(ctx),
  );
  const raw = listRowsFromEnvelope(response);
  return {
    items: raw.map((t) => ({
      id: String(t.id),
      code: String(t.code),
      name: String(t.name),
      category: t.category != null ? String(t.category) : null,
      sample_type: t.sample_type != null ? String(t.sample_type) : null,
      turnaround_hours:
        t.turnaround_hours != null && Number.isFinite(Number(t.turnaround_hours))
          ? Number(t.turnaround_hours)
          : null,
      price: t.price != null ? Number(t.price) : t.price_display != null ? Number(t.price_display) : null,
    })),
    total: paginationTotal(response, raw.length),
  };
}

/** POST /api/v1/reception/workspace/orders — pricing in response is authoritative */
export async function createReceptionOrder(
  ctx: Ctx,
  payload: {
    patient_code: string;
    test_catalog_ids: string[];
    discount?: number;
    note?: string;
    queue_entry_id?: string;
  },
): Promise<ReceptionOrderCreate> {
  const uniqueTestIds = Array.from(new Set(payload.test_catalog_ids.filter(Boolean)));
  const response = await apiRequest<{ success: boolean; data: ReceptionOrderCreate }>(
    "/api/v1/reception/workspace/orders",
    {
      ...requestOpts(ctx, {
        method: "POST",
        body: {
          patient_code: payload.patient_code,
          test_catalog_ids: uniqueTestIds,
          discount: payload.discount ?? 0,
          note: payload.note,
          queue_entry_id: payload.queue_entry_id,
        },
      }),
    },
  );
  const data = response.data;
  return {
    order: data.order,
    invoice: data.invoice,
    pricing: mapPricing(data.pricing as unknown as Record<string, unknown>),
  };
}

/**
 * GET /api/v1/reception/workspace/orders/:ref — reopen / refresh persistence.
 * If that route is not yet deployed (404), optionally resolve via patient profile
 * `orders[]` when `patientCode` is provided (production-safe fallback).
 */
export async function fetchReceptionOrder(
  ctx: Ctx,
  orderRef: string,
  opts?: { patientCode?: string },
): Promise<ReceptionOrderDetail> {
  try {
    const response = await apiRequest<{ success: boolean; data: ReceptionOrderDetail }>(
      `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}`,
      requestOpts(ctx),
    );
    const data = response.data as unknown as Record<string, unknown>;
    const pricing = mapPricing(data.pricing as Record<string, unknown> | undefined);
    return {
      order: (data.order as Record<string, unknown>) ?? response.data.order,
      pricing,
      payment_summary: mapPaymentSummary(
        data.payment_summary as Record<string, unknown> | undefined,
        pricing,
      ),
      payment: mapPaymentRecord(data.payment as Record<string, unknown> | undefined),
      invoice:
        data.invoice && typeof data.invoice === "object"
          ? (data.invoice as Record<string, unknown>)
          : null,
    };
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404 || !opts?.patientCode) {
      throw error;
    }
    const profile = await fetchReceptionPatient(ctx, opts.patientCode);
    const match = (profile.orders ?? []).find((row) => {
      const code = String(row.order_code ?? row.id ?? "");
      return code === orderRef;
    });
    if (!match) {
      throw new ApiError("Order not found on patient profile", 404, {
        code: "ORDER_NOT_FOUND",
        error: "Order not found on patient profile",
      });
    }
    return {
      order: {
        ...match,
        order_code: match.order_code ?? orderRef,
        patient_code: profile.patient_code,
        patient_name: profile.full_name,
      },
      pricing: mapPricing({
        subtotal: match.subtotal,
        discount: match.discount,
        total: match.total_amount ?? match.total,
        tax: match.tax,
      }),
    };
  }
}


function mapPaymentSummary(
  raw: Record<string, unknown> | undefined | null,
  pricingFallback?: ReceptionOrderPricing,
): ReceptionPaymentSummary {
  const source = raw ?? {};
  const total = Number(source.order_total ?? pricingFallback?.total ?? 0);
  const paid = Number(source.paid_amount ?? 0);
  const outstanding = Number(
    source.outstanding_amount ?? Math.max(0, total - paid),
  );
  return {
    order_total: total,
    paid_amount: paid,
    outstanding_amount: outstanding,
    discount: source.discount != null ? Number(source.discount) : pricingFallback?.discount,
    subtotal: source.subtotal != null ? Number(source.subtotal) : pricingFallback?.subtotal,
    tax: source.tax != null ? Number(source.tax) : pricingFallback?.tax ?? null,
    status: String(source.status ?? (paid > 0 && outstanding <= 0 ? "paid" : "unpaid")),
    payment_methods_supported: Array.isArray(source.payment_methods_supported)
      ? (source.payment_methods_supported as string[])
      : [...RECEPTION_PAYMENT_METHODS],
    partial_payments_supported: Boolean(source.partial_payments_supported),
  };
}

function mapPaymentRecord(raw: Record<string, unknown> | null | undefined): ReceptionPaymentRecord | null {
  if (!raw) return null;
  const receipt = raw.receipt_number ?? raw.receiptNumber;
  if (!receipt) return null;
  return {
    id: raw.id != null ? String(raw.id) : undefined,
    receipt_number: String(receipt),
    payment_method: String(raw.payment_method ?? "cash"),
    amount: Number(raw.amount ?? 0),
    paid_at: raw.paid_at != null ? String(raw.paid_at) : null,
    created_by: raw.created_by != null ? String(raw.created_by) : null,
  };
}

function mapBarcodes(raw: Record<string, unknown>): ReceptionBarcodes {
  const samples = Array.isArray(raw.sample_barcodes)
    ? (raw.sample_barcodes as Record<string, unknown>[]).map((s) => ({
        test_code: String(s.test_code ?? ""),
        test_name: String(s.test_name ?? ""),
        sample_type: s.sample_type != null ? String(s.sample_type) : undefined,
        specimen_code: s.specimen_code != null ? String(s.specimen_code) : undefined,
        barcode: String(s.barcode ?? ""),
        collection_requirement:
          s.collection_requirement != null ? String(s.collection_requirement) : undefined,
      }))
    : [];
  return {
    order_code: raw.order_code != null ? String(raw.order_code) : undefined,
    patient_code: raw.patient_code != null ? String(raw.patient_code) : undefined,
    patient_name: raw.patient_name != null ? String(raw.patient_name) : null,
    order_barcode: String(raw.order_barcode ?? ""),
    patient_barcode: String(raw.patient_barcode ?? ""),
    patient_qr: String(raw.patient_qr ?? ""),
    sample_barcodes: samples,
    collection_barcode: raw.collection_barcode != null ? String(raw.collection_barcode) : null,
    generated_at: raw.generated_at != null ? String(raw.generated_at) : undefined,
    reprint: Boolean(raw.reprint),
    status: raw.status != null ? String(raw.status) : undefined,
  };
}

export function isValidPatientQr(payload: string): boolean {
  return payload.startsWith(PATIENT_QR_PREFIX) && payload.length > PATIENT_QR_PREFIX.length;
}


/** POST /api/v1/reception/workspace/orders/:ref/payment */
export async function collectReceptionPayment(
  ctx: Ctx,
  orderRef: string,
  payload: {
    payment_method: string;
    amount: number;
    receipt_number?: string;
    idempotency_key: string;
  },
): Promise<ReceptionPaymentResult> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/payment`,
    requestOpts(ctx, {
      method: "POST",
      timeoutMs: ctx.timeoutMs ?? RECEPTION_PAYMENT_TIMEOUT_MS,
      headers: { "Idempotency-Key": payload.idempotency_key },
      body: {
        payment_method: payload.payment_method,
        amount: payload.amount,
        receipt_number: payload.receipt_number ?? payload.idempotency_key,
        idempotency_key: payload.idempotency_key,
      },
    }),
  );
  const data = response.data ?? {};
  return {
    payment: mapPaymentRecord(data.payment as Record<string, unknown> | undefined),
    invoice:
      data.invoice && typeof data.invoice === "object"
        ? (data.invoice as Record<string, unknown>)
        : null,
    order_status: data.order_status != null ? String(data.order_status) : null,
    payment_summary: mapPaymentSummary(data.payment_summary as Record<string, unknown> | undefined),
    idempotent_replay: Boolean(data.idempotent_replay),
  };
}

/** GET /api/v1/reception/workspace/orders/:ref/barcode */
export async function fetchReceptionBarcodes(
  ctx: Ctx,
  orderRef: string,
): Promise<ReceptionBarcodes> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/barcode`,
    requestOpts(ctx),
  );
  return mapBarcodes(response.data ?? {});
}

/** GET /api/v1/reception/workspace/orders/:ref/request-form */
export async function fetchReceptionRequestForm(
  ctx: Ctx,
  orderRef: string,
): Promise<ReceptionRequestForm> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/request-form`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    html: String(data.html ?? ""),
    order_code: data.order_code != null ? String(data.order_code) : undefined,
    patient_code: data.patient_code != null ? String(data.patient_code) : undefined,
    barcodes: data.barcodes && typeof data.barcodes === "object"
      ? mapBarcodes(data.barcodes as Record<string, unknown>)
      : undefined,
    reprint: Boolean(data.reprint),
    generated_at: data.generated_at != null ? String(data.generated_at) : undefined,
  };
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

export function catalogCategories(tests: ReceptionTest[]): string[] {
  return Array.from(
    new Set(tests.map((t) => t.category).filter(Boolean) as string[]),
  ).sort();
}
