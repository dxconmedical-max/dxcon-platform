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
  payments?: ReceptionPaymentRecord[];
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
  payments?: ReceptionPaymentRecord[];
  receipt?: Record<string, unknown> | null;
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

export type ReceptionLabHandoff = {
  order_code: string;
  order_status: string | null;
  collection: Record<string, unknown> | null;
  queue_entry: Record<string, unknown> | null;
  queue_reference: string | null;
  laboratory: { id: string | null; name: string };
  accepted_at: string | null;
  barcodes?: {
    order_barcode?: string | null;
    patient_qr?: string | null;
    sample_count?: number;
  };
  handed_off?: boolean;
  idempotent_replay?: boolean;
  actor?: string | null;
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
export const RECEPTION_LAB_HANDOFF_TIMEOUT_MS = 30_000;

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
      payments: Array.isArray(data.payments)
        ? (data.payments as Record<string, unknown>[])
            .map((row) => mapPaymentRecord(row))
            .filter((row): row is ReceptionPaymentRecord => row != null)
        : undefined,
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

export const QR_KIND_OPTIONS = [
  "payment",
  "vnpay",
  "static",
  "dynamic",
  "sample",
  "tracking",
] as const;

export type ReceptionQrKind = (typeof QR_KIND_OPTIONS)[number];

export type ReceptionQrCard = {
  kind: string;
  title: string;
  payload: string | null;
  static: boolean;
  image_data_url?: string | null;
  unavailable?: boolean;
  meta?: Record<string, unknown>;
};

export type ReceptionQrBundle = {
  order_code: string;
  patient_code?: string;
  patient_name?: string;
  status?: string;
  generated_at?: string;
  kinds: string[];
  qrs: ReceptionQrCard[];
  html?: string;
};

export type ReceptionQrVerifyResult = {
  payload: string;
  valid: boolean;
  kind: string | null;
  reason: string | null;
  fields: Record<string, unknown>;
};

function mapQrCard(raw: Record<string, unknown>): ReceptionQrCard {
  return {
    kind: String(raw.kind ?? ""),
    title: String(raw.title ?? ""),
    payload: raw.payload == null ? null : String(raw.payload),
    static: Boolean(raw.static),
    image_data_url: raw.image_data_url != null ? String(raw.image_data_url) : null,
    unavailable: Boolean(raw.unavailable),
    meta: (raw.meta as Record<string, unknown> | undefined) ?? {},
  };
}

function mapQrBundle(data: Record<string, unknown>): ReceptionQrBundle {
  return {
    order_code: data.order_code != null ? String(data.order_code) : "",
    patient_code: data.patient_code != null ? String(data.patient_code) : undefined,
    patient_name: data.patient_name != null ? String(data.patient_name) : undefined,
    status: data.status != null ? String(data.status) : undefined,
    generated_at: data.generated_at != null ? String(data.generated_at) : undefined,
    kinds: Array.isArray(data.kinds) ? data.kinds.map(String) : [],
    qrs: Array.isArray(data.qrs)
      ? (data.qrs as Record<string, unknown>[]).map(mapQrCard)
      : [],
    html: data.html != null ? String(data.html) : undefined,
  };
}

/** GET /api/v1/reception/workspace/orders/:ref/qr */
export async function fetchReceptionQrBundle(
  ctx: Ctx,
  orderRef: string,
  opts?: { kinds?: string[]; amount?: number; images?: boolean; preview?: boolean },
): Promise<ReceptionQrBundle> {
  const params = new URLSearchParams();
  if (opts?.kinds?.length) params.set("kinds", opts.kinds.join(","));
  if (opts?.amount != null) params.set("amount", String(opts.amount));
  if (opts?.images === false) params.set("images", "0");
  if (opts?.preview) params.set("preview", "1");
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/qr${qs}`,
    requestOpts(ctx),
  );
  return mapQrBundle(response.data ?? {});
}

/** GET /api/v1/reception/workspace/orders/:ref/qr/preview */
export async function previewReceptionQrBundle(
  ctx: Ctx,
  orderRef: string,
  opts?: { kinds?: string[]; amount?: number },
): Promise<ReceptionQrBundle> {
  const params = new URLSearchParams();
  if (opts?.kinds?.length) params.set("kinds", opts.kinds.join(","));
  if (opts?.amount != null) params.set("amount", String(opts.amount));
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/qr/preview${qs}`,
    requestOpts(ctx),
  );
  return mapQrBundle(response.data ?? {});
}

/** POST /api/v1/reception/workspace/qr/verify */
export async function verifyReceptionQr(
  ctx: Ctx,
  payload: string,
  orderRef?: string,
): Promise<ReceptionQrVerifyResult> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/qr/verify`,
    requestOpts(ctx, {
      method: "POST",
      body: { payload, order_ref: orderRef },
    }),
  );
  const data = response.data ?? {};
  return {
    payload: String(data.payload ?? payload),
    valid: Boolean(data.valid),
    kind: data.kind != null ? String(data.kind) : null,
    reason: data.reason != null ? String(data.reason) : null,
    fields: (data.fields as Record<string, unknown> | undefined) ?? {},
  };
}

/** GET /api/v1/reception/workspace/qr/kinds */
export async function fetchReceptionQrKinds(ctx: Ctx) {
  const response = await apiRequest<{ success: boolean; data: { kinds?: unknown[] } }>(
    `/api/v1/reception/workspace/qr/kinds`,
    requestOpts(ctx),
  );
  return Array.isArray(response.data?.kinds) ? response.data!.kinds! : [];
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
    payments: Array.isArray(data.payments)
      ? (data.payments as Record<string, unknown>[])
          .map((row) => mapPaymentRecord(row))
          .filter((row): row is ReceptionPaymentRecord => row != null)
      : undefined,
    receipt:
      data.receipt && typeof data.receipt === "object"
        ? (data.receipt as Record<string, unknown>)
        : null,
    invoice:
      data.invoice && typeof data.invoice === "object"
        ? (data.invoice as Record<string, unknown>)
        : null,
    order_status: data.order_status != null ? String(data.order_status) : null,
    payment_summary: mapPaymentSummary(data.payment_summary as Record<string, unknown> | undefined),
    idempotent_replay: Boolean(data.idempotent_replay),
  };
}

export type ReceptionReceiptRecord = {
  id?: string;
  receipt_code: string;
  payment_id: string;
  order_id: string;
  status: string;
  print_count: number;
  preferred_format?: string;
  pdf_available?: boolean;
  issued_at?: string | null;
  issued_by?: string | null;
  last_printed_at?: string | null;
  cancel_reason?: string | null;
};

function mapReceiptRecord(raw: Record<string, unknown> | null | undefined): ReceptionReceiptRecord | null {
  if (!raw || raw.receipt_code == null) return null;
  return {
    id: raw.id != null ? String(raw.id) : undefined,
    receipt_code: String(raw.receipt_code),
    payment_id: String(raw.payment_id ?? ""),
    order_id: String(raw.order_id ?? ""),
    status: String(raw.status ?? "issued"),
    print_count: Number(raw.print_count ?? 0),
    preferred_format: raw.preferred_format != null ? String(raw.preferred_format) : undefined,
    pdf_available: Boolean(raw.pdf_available),
    issued_at: raw.issued_at != null ? String(raw.issued_at) : null,
    issued_by: raw.issued_by != null ? String(raw.issued_by) : null,
    last_printed_at: raw.last_printed_at != null ? String(raw.last_printed_at) : null,
    cancel_reason: raw.cancel_reason != null ? String(raw.cancel_reason) : null,
  };
}

/** GET /api/v1/reception/workspace/receipts/:ref */
export async function fetchReceptionReceipt(ctx: Ctx, receiptRef: string) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/receipts/${encodeURIComponent(receiptRef)}`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  const preview = (data.preview as Record<string, unknown> | undefined) ?? {};
  return {
    receipt: mapReceiptRecord(data.receipt as Record<string, unknown>),
    payment: mapPaymentRecord(data.payment as Record<string, unknown> | undefined),
    preview: {
      html: String(preview.html ?? ""),
      thermal_text: preview.thermal_text != null ? String(preview.thermal_text) : undefined,
      thermal_html: preview.thermal_html != null ? String(preview.thermal_html) : undefined,
      context: (preview.context as Record<string, unknown> | undefined) ?? undefined,
    },
  };
}

/** GET /api/v1/reception/workspace/receipts/:ref/preview */
export async function previewReceptionReceipt(
  ctx: Ctx,
  receiptRef: string,
  format: "standard" | "thermal" = "standard",
) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/receipts/${encodeURIComponent(receiptRef)}/preview?format=${format}`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    receipt_code: String(data.receipt_code ?? receiptRef),
    status: String(data.status ?? ""),
    format: String(data.format ?? format),
    html: String(data.html ?? ""),
    thermal_text: data.thermal_text != null ? String(data.thermal_text) : undefined,
    context: (data.context as Record<string, unknown> | undefined) ?? undefined,
  };
}

/** POST /api/v1/reception/workspace/receipts/:ref/print */
export async function printReceptionReceipt(
  ctx: Ctx,
  receiptRef: string,
  format: "standard" | "thermal" = "standard",
) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/receipts/${encodeURIComponent(receiptRef)}/print`,
    requestOpts(ctx, { method: "POST", body: { format } }),
  );
  const data = response.data ?? {};
  const preview = (data.preview as Record<string, unknown> | undefined) ?? {};
  return {
    receipt: mapReceiptRecord(data.receipt as Record<string, unknown>),
    preview: {
      html: String(preview.html ?? ""),
      thermal_text: preview.thermal_text != null ? String(preview.thermal_text) : undefined,
      thermal_html: preview.thermal_html != null ? String(preview.thermal_html) : undefined,
    },
  };
}

/** POST /api/v1/reception/workspace/receipts/:ref/reprint */
export async function reprintReceptionReceipt(
  ctx: Ctx,
  receiptRef: string,
  format: "standard" | "thermal" = "standard",
) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/receipts/${encodeURIComponent(receiptRef)}/reprint`,
    requestOpts(ctx, { method: "POST", body: { format } }),
  );
  const data = response.data ?? {};
  const preview = (data.preview as Record<string, unknown> | undefined) ?? {};
  return {
    receipt: mapReceiptRecord(data.receipt as Record<string, unknown>),
    preview: {
      html: String(preview.html ?? ""),
      thermal_text: preview.thermal_text != null ? String(preview.thermal_text) : undefined,
      thermal_html: preview.thermal_html != null ? String(preview.thermal_html) : undefined,
    },
  };
}

/** POST /api/v1/reception/workspace/receipts/:ref/cancel */
export async function cancelReceptionReceipt(
  ctx: Ctx,
  receiptRef: string,
  reason?: string,
) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/receipts/${encodeURIComponent(receiptRef)}/cancel`,
    requestOpts(ctx, { method: "POST", body: { reason } }),
  );
  const data = response.data ?? {};
  return {
    receipt: mapReceiptRecord(data.receipt as Record<string, unknown>),
    idempotent_replay: Boolean(data.idempotent_replay),
  };
}

/** GET /api/v1/reception/workspace/orders/:ref/receipts */
export async function fetchOrderReceipts(ctx: Ctx, orderRef: string) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/receipts`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    order_code: String(data.order_code ?? orderRef),
    receipts: Array.isArray(data.receipts)
      ? (data.receipts as Record<string, unknown>[])
          .map((row) => mapReceiptRecord(row))
          .filter((row): row is ReceptionReceiptRecord => row != null)
      : [],
  };
}

/** Absolute path helper for PDF download (browser opens with auth cookie/session). */
export function receptionReceiptPdfUrl(receiptRef: string): string {
  return `/api/v1/reception/workspace/receipts/${encodeURIComponent(receiptRef)}/pdf`;
}

/** GET /api/v1/reception/workspace/orders/:ref/payments */
export async function fetchReceptionPaymentHistory(
  ctx: Ctx,
  orderRef: string,
): Promise<{
  order_code: string;
  payment_summary: ReceptionPaymentSummary;
  payments: ReceptionPaymentRecord[];
}> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/payments`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    order_code: String(data.order_code ?? orderRef),
    payment_summary: mapPaymentSummary(
      data.payment_summary as Record<string, unknown> | undefined,
    ),
    payments: Array.isArray(data.payments)
      ? (data.payments as Record<string, unknown>[])
          .map((row) => mapPaymentRecord(row))
          .filter((row): row is ReceptionPaymentRecord => row != null)
      : [],
  };
}

/** GET /api/v1/reception/workspace/orders/:ref/barcode */
export async function fetchReceptionBarcodes(
  ctx: Ctx,
  orderRef: string,
  opts?: { labels?: boolean },
): Promise<ReceptionBarcodes & { labels?: Record<string, unknown>[] }> {
  const qs = opts?.labels ? "?labels=1" : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/barcode${qs}`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  if (data.barcodes && typeof data.barcodes === "object") {
    return {
      ...mapBarcodes(data.barcodes as Record<string, unknown>),
      labels: Array.isArray(data.labels) ? (data.labels as Record<string, unknown>[]) : undefined,
    };
  }
  const mapped = mapBarcodes(data);
  if (Array.isArray(data.labels)) {
    return { ...mapped, labels: data.labels as Record<string, unknown>[] };
  }
  return mapped;
}

/** GET /api/v1/reception/workspace/orders/:ref/barcode/labels */
export async function fetchReceptionBarcodeLabels(
  ctx: Ctx,
  orderRef: string,
  types?: string[],
) {
  const qs = types?.length ? `?types=${encodeURIComponent(types.join(","))}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/barcode/labels${qs}`,
    requestOpts(ctx),
  );
  return response.data ?? {};
}

/** GET /api/v1/reception/workspace/orders/:ref/barcode/preview */
export async function previewReceptionBarcodeLabels(
  ctx: Ctx,
  orderRef: string,
  opts?: { types?: string[]; format?: "standard" | "thermal" },
) {
  const params = new URLSearchParams();
  if (opts?.types?.length) params.set("types", opts.types.join(","));
  if (opts?.format) params.set("format", opts.format);
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/barcode/preview${qs}`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    order_code: data.order_code != null ? String(data.order_code) : orderRef,
    format: String(data.format ?? opts?.format ?? "standard"),
    html: String(data.html ?? ""),
    thermal_text: data.thermal_text != null ? String(data.thermal_text) : "",
    labels: Array.isArray(data.labels) ? (data.labels as Record<string, unknown>[]) : [],
    printers: Array.isArray(data.printers) ? data.printers : [],
    printable_count: Number(data.printable_count ?? 0),
  };
}

/** POST /api/v1/reception/workspace/orders/:ref/barcode/print */
export async function printReceptionBarcodeLabels(
  ctx: Ctx,
  orderRef: string,
  payload?: {
    types?: string[];
    format?: "standard" | "thermal";
    printer?: "browser" | "thermal";
  },
) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/barcode/print`,
    requestOpts(ctx, {
      method: "POST",
      body: {
        types: payload?.types,
        format: payload?.format ?? "standard",
        printer: payload?.printer ?? "browser",
      },
    }),
  );
  const data = response.data ?? {};
  const job = (data.job as Record<string, unknown> | undefined) ?? {};
  return {
    order_code: data.order_code != null ? String(data.order_code) : orderRef,
    format: String(data.format ?? "standard"),
    job: {
      job_id: String(job.job_id ?? ""),
      printer: String(job.printer ?? ""),
      media: String(job.media ?? ""),
      title: String(job.title ?? ""),
      html: String(job.html ?? ""),
      thermal_text: String(job.thermal_text ?? ""),
    },
    labels: Array.isArray(data.labels) ? (data.labels as Record<string, unknown>[]) : [],
  };
}

/** GET /api/v1/reception/workspace/barcode/printers */
export async function fetchReceptionBarcodePrinters(ctx: Ctx) {
  const response = await apiRequest<{ success: boolean; data: { printers?: unknown[] } }>(
    `/api/v1/reception/workspace/barcode/printers`,
    requestOpts(ctx),
  );
  return Array.isArray(response.data?.printers) ? response.data!.printers! : [];
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

function mapLabHandoff(raw: Record<string, unknown>): ReceptionLabHandoff {
  const laboratory =
    raw.laboratory && typeof raw.laboratory === "object"
      ? (raw.laboratory as Record<string, unknown>)
      : {};
  return {
    order_code: String(raw.order_code ?? ""),
    order_status: raw.order_status != null ? String(raw.order_status) : null,
    collection:
      raw.collection && typeof raw.collection === "object"
        ? (raw.collection as Record<string, unknown>)
        : null,
    queue_entry:
      raw.queue_entry && typeof raw.queue_entry === "object"
        ? (raw.queue_entry as Record<string, unknown>)
        : null,
    queue_reference: raw.queue_reference != null ? String(raw.queue_reference) : null,
    laboratory: {
      id: laboratory.id != null ? String(laboratory.id) : null,
      name: String(laboratory.name ?? "Central Laboratory"),
    },
    accepted_at: raw.accepted_at != null ? String(raw.accepted_at) : null,
    barcodes:
      raw.barcodes && typeof raw.barcodes === "object"
        ? {
            order_barcode: (raw.barcodes as Record<string, unknown>).order_barcode != null
              ? String((raw.barcodes as Record<string, unknown>).order_barcode)
              : null,
            patient_qr: (raw.barcodes as Record<string, unknown>).patient_qr != null
              ? String((raw.barcodes as Record<string, unknown>).patient_qr)
              : null,
            sample_count: Number(
              (raw.barcodes as Record<string, unknown>).sample_count ?? 0,
            ),
          }
        : undefined,
    handed_off: Boolean(
      raw.handed_off ??
        (raw.order_status === "lab_received" || raw.order_status === "testing"),
    ),
    idempotent_replay: Boolean(raw.idempotent_replay),
    actor: raw.actor != null ? String(raw.actor) : null,
  };
}

/** POST /api/v1/reception/workspace/orders/:ref/lab-handoff */
export async function handoffReceptionOrderToLab(
  ctx: Ctx,
  orderRef: string,
  payload: {
    laboratory_name?: string;
    laboratory_id?: string | null;
    collector_name?: string;
    pickup_address?: string;
  } = {},
): Promise<ReceptionLabHandoff> {
  try {
    const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
      `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/lab-handoff`,
      requestOpts(ctx, {
        method: "POST",
        timeoutMs: ctx.timeoutMs ?? RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
        body: {
          laboratory_name: payload.laboratory_name ?? "Central Laboratory",
          laboratory_id: payload.laboratory_id ?? undefined,
          collector_name: payload.collector_name ?? "Reception Desk",
          pickup_address: payload.pickup_address ?? "Reception Desk",
        },
      }),
    );
    return mapLabHandoff(response.data ?? {});
  } catch (error) {
    if (error instanceof ApiError) {
      const body =
        error.body && typeof error.body === "object"
          ? (error.body as Record<string, unknown>)
          : {};
      const message =
        (typeof body.error === "string" && body.error) ||
        error.message ||
        "Laboratory handoff failed";
      throw new ApiError(message, error.status, {
        ...body,
        error: message,
        code: typeof body.code === "string" ? body.code : "LAB_HANDOFF_FAILED",
      });
    }
    throw error;
  }
}

/** GET /api/v1/reception/workspace/orders/:ref/lab-handoff */
export async function fetchReceptionLabHandoff(
  ctx: Ctx,
  orderRef: string,
): Promise<ReceptionLabHandoff> {
  try {
    const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
      `/api/v1/reception/workspace/orders/${encodeURIComponent(orderRef)}/lab-handoff`,
      requestOpts(ctx, {
        timeoutMs: ctx.timeoutMs ?? RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
      }),
    );
    return mapLabHandoff(response.data ?? {});
  } catch (error) {
    if (error instanceof ApiError) {
      const body =
        error.body && typeof error.body === "object"
          ? (error.body as Record<string, unknown>)
          : {};
      const message =
        (typeof body.error === "string" && body.error) ||
        error.message ||
        "Failed to load laboratory handoff status";
      throw new ApiError(message, error.status, {
        ...body,
        error: message,
        code: typeof body.code === "string" ? body.code : "LAB_HANDOFF_STATUS_FAILED",
      });
    }
    throw error;
  }
}

export type LabQueueStage = "waiting" | "processing" | "completed" | "verified";
export type LabQueuePriority = "urgent" | "high" | "routine" | "low";

export type LabQueueItem = {
  id: string;
  order_code: string;
  stage: string;
  priority: string;
  patient_code?: string;
  patient_name?: string;
  order_status?: string;
  queue_reference?: string | null;
  laboratory_name?: string | null;
  entered_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  verified_at?: string | null;
  tests?: { test_code?: string; test_name?: string }[];
};

export type LabQueueStatistics = {
  by_stage: Record<string, number>;
  by_priority: Record<string, number>;
  total_queued: number;
  active: number;
  waiting: number;
  processing: number;
  completed: number;
  verified: number;
  paid_not_queued: number;
  barcode_ready_not_queued: number;
  pipeline: string[];
  priorities: string[];
  stages: string[];
};

export type LabQueueDashboard = {
  items: LabQueueItem[];
  statistics: LabQueueStatistics;
  refreshed_at: string;
  version: number;
  changed: boolean;
  workflow: string[];
  transitions: Record<string, string[]>;
  priorities: string[];
};

function mapLabQueueItem(raw: Record<string, unknown>): LabQueueItem {
  return {
    id: String(raw.id ?? ""),
    order_code: String(raw.order_code ?? ""),
    stage: String(raw.stage ?? ""),
    priority: String(raw.priority ?? "routine"),
    patient_code: raw.patient_code != null ? String(raw.patient_code) : undefined,
    patient_name: raw.patient_name != null ? String(raw.patient_name) : undefined,
    order_status: raw.order_status != null ? String(raw.order_status) : undefined,
    queue_reference: raw.queue_reference != null ? String(raw.queue_reference) : null,
    laboratory_name: raw.laboratory_name != null ? String(raw.laboratory_name) : null,
    entered_at: raw.entered_at != null ? String(raw.entered_at) : null,
    started_at: raw.started_at != null ? String(raw.started_at) : null,
    completed_at: raw.completed_at != null ? String(raw.completed_at) : null,
    verified_at: raw.verified_at != null ? String(raw.verified_at) : null,
    tests: Array.isArray(raw.tests)
      ? (raw.tests as Record<string, unknown>[]).map((t) => ({
          test_code: t.test_code != null ? String(t.test_code) : undefined,
          test_name: t.test_name != null ? String(t.test_name) : undefined,
        }))
      : [],
  };
}

function mapLabQueueDashboard(data: Record<string, unknown>): LabQueueDashboard {
  const stats = (data.statistics as Record<string, unknown> | undefined) ?? {};
  return {
    items: Array.isArray(data.items)
      ? (data.items as Record<string, unknown>[]).map(mapLabQueueItem)
      : [],
    statistics: {
      by_stage: (stats.by_stage as Record<string, number>) ?? {},
      by_priority: (stats.by_priority as Record<string, number>) ?? {},
      total_queued: Number(stats.total_queued ?? 0),
      active: Number(stats.active ?? 0),
      waiting: Number(stats.waiting ?? 0),
      processing: Number(stats.processing ?? 0),
      completed: Number(stats.completed ?? 0),
      verified: Number(stats.verified ?? 0),
      paid_not_queued: Number(stats.paid_not_queued ?? 0),
      barcode_ready_not_queued: Number(stats.barcode_ready_not_queued ?? 0),
      pipeline: Array.isArray(stats.pipeline) ? stats.pipeline.map(String) : [],
      priorities: Array.isArray(stats.priorities) ? stats.priorities.map(String) : [],
      stages: Array.isArray(stats.stages) ? stats.stages.map(String) : [],
    },
    refreshed_at: String(data.refreshed_at ?? ""),
    version: Number(data.version ?? 0),
    changed: data.changed !== false,
    workflow: Array.isArray(data.workflow) ? data.workflow.map(String) : [],
    transitions: (data.transitions as Record<string, string[]>) ?? {},
    priorities: Array.isArray(data.priorities) ? data.priorities.map(String) : [],
  };
}

/** GET /api/v1/reception/workspace/lab-queue */
export async function fetchLabQueueDashboard(
  ctx: Ctx,
  opts?: {
    stage?: string;
    priority?: string;
    since?: string;
    version?: number;
    limit?: number;
  },
): Promise<LabQueueDashboard> {
  const params = new URLSearchParams();
  if (opts?.stage) params.set("stage", opts.stage);
  if (opts?.priority) params.set("priority", opts.priority);
  if (opts?.since) params.set("since", opts.since);
  if (opts?.version != null) params.set("version", String(opts.version));
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/lab-queue${qs}`,
    requestOpts(ctx),
  );
  return mapLabQueueDashboard(response.data ?? {});
}

/** GET /api/v1/reception/workspace/lab-queue/refresh */
export async function refreshLabQueue(
  ctx: Ctx,
  opts?: { since?: string; version?: number },
): Promise<LabQueueDashboard> {
  const params = new URLSearchParams();
  if (opts?.since) params.set("since", opts.since);
  if (opts?.version != null) params.set("version", String(opts.version));
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/lab-queue/refresh${qs}`,
    requestOpts(ctx),
  );
  return mapLabQueueDashboard(response.data ?? {});
}

/** GET /api/v1/reception/workspace/lab-queue/stats */
export async function fetchLabQueueStats(ctx: Ctx): Promise<LabQueueStatistics> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/lab-queue/stats`,
    requestOpts(ctx),
  );
  const stats = response.data ?? {};
  return {
    by_stage: (stats.by_stage as Record<string, number>) ?? {},
    by_priority: (stats.by_priority as Record<string, number>) ?? {},
    total_queued: Number(stats.total_queued ?? 0),
    active: Number(stats.active ?? 0),
    waiting: Number(stats.waiting ?? 0),
    processing: Number(stats.processing ?? 0),
    completed: Number(stats.completed ?? 0),
    verified: Number(stats.verified ?? 0),
    paid_not_queued: Number(stats.paid_not_queued ?? 0),
    barcode_ready_not_queued: Number(stats.barcode_ready_not_queued ?? 0),
    pipeline: Array.isArray(stats.pipeline) ? stats.pipeline.map(String) : [],
    priorities: Array.isArray(stats.priorities) ? stats.priorities.map(String) : [],
    stages: Array.isArray(stats.stages) ? stats.stages.map(String) : [],
  };
}

/** POST /api/v1/reception/workspace/lab-queue/orders/:ref/enqueue */
export async function enqueueLabQueueOrder(
  ctx: Ctx,
  orderRef: string,
  payload?: { priority?: string; laboratory_name?: string },
) {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/lab-queue/orders/${encodeURIComponent(orderRef)}/enqueue`,
    requestOpts(ctx, {
      method: "POST",
      body: {
        priority: payload?.priority,
        laboratory_name: payload?.laboratory_name,
      },
    }),
  );
  return response.data ?? {};
}

/** POST /api/v1/reception/workspace/lab-queue/orders/:ref/advance */
export async function advanceLabQueueOrder(
  ctx: Ctx,
  orderRef: string,
  to: LabQueueStage | string,
): Promise<LabQueueItem> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/lab-queue/orders/${encodeURIComponent(orderRef)}/advance`,
    requestOpts(ctx, { method: "POST", body: { to } }),
  );
  return mapLabQueueItem(response.data ?? {});
}

/** POST /api/v1/reception/workspace/lab-queue/orders/:ref/priority */
export async function setLabQueuePriority(
  ctx: Ctx,
  orderRef: string,
  priority: LabQueuePriority | string,
): Promise<LabQueueItem> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/lab-queue/orders/${encodeURIComponent(orderRef)}/priority`,
    requestOpts(ctx, { method: "POST", body: { priority } }),
  );
  return mapLabQueueItem(response.data ?? {});
}

export type SampleQueueStage =
  | "collected"
  | "transport"
  | "received"
  | "sorting"
  | "laboratory"
  | "completed";

export type SampleQueueEvent = {
  id: string;
  order_code: string;
  event_type: string;
  from_stage?: string | null;
  to_stage?: string | null;
  actor?: string | null;
  location?: string | null;
  note?: string | null;
  created_at?: string | null;
};

export type SampleQueueItem = {
  id: string;
  order_code: string;
  stage: string;
  sample_code?: string | null;
  patient_code?: string;
  patient_name?: string;
  order_status?: string;
  collection_status?: string | null;
  location?: string | null;
  collector_name?: string | null;
  next_stage?: string | null;
  history?: SampleQueueEvent[];
  collected_at?: string | null;
  transport_at?: string | null;
  received_at?: string | null;
  sorting_at?: string | null;
  laboratory_at?: string | null;
  completed_at?: string | null;
};

export type SampleQueueStatistics = {
  by_stage: Record<string, number>;
  total: number;
  active: number;
  in_transit: number;
  completed: number;
  pipeline: string[];
  stages: string[];
};

export type SampleQueueDashboard = {
  items: SampleQueueItem[];
  statistics: SampleQueueStatistics;
  refreshed_at: string;
  version: number;
  changed: boolean;
  workflow: string[];
  transitions: Record<string, string[]>;
};

function mapSampleQueueEvent(raw: Record<string, unknown>): SampleQueueEvent {
  return {
    id: String(raw.id ?? ""),
    order_code: String(raw.order_code ?? ""),
    event_type: String(raw.event_type ?? ""),
    from_stage: raw.from_stage != null ? String(raw.from_stage) : null,
    to_stage: raw.to_stage != null ? String(raw.to_stage) : null,
    actor: raw.actor != null ? String(raw.actor) : null,
    location: raw.location != null ? String(raw.location) : null,
    note: raw.note != null ? String(raw.note) : null,
    created_at: raw.created_at != null ? String(raw.created_at) : null,
  };
}

function mapSampleQueueItem(raw: Record<string, unknown>): SampleQueueItem {
  return {
    id: String(raw.id ?? ""),
    order_code: String(raw.order_code ?? ""),
    stage: String(raw.stage ?? ""),
    sample_code: raw.sample_code != null ? String(raw.sample_code) : null,
    patient_code: raw.patient_code != null ? String(raw.patient_code) : undefined,
    patient_name: raw.patient_name != null ? String(raw.patient_name) : undefined,
    order_status: raw.order_status != null ? String(raw.order_status) : undefined,
    collection_status: raw.collection_status != null ? String(raw.collection_status) : null,
    location: raw.location != null ? String(raw.location) : null,
    collector_name: raw.collector_name != null ? String(raw.collector_name) : null,
    next_stage: raw.next_stage != null ? String(raw.next_stage) : null,
    history: Array.isArray(raw.history)
      ? (raw.history as Record<string, unknown>[]).map(mapSampleQueueEvent)
      : undefined,
    collected_at: raw.collected_at != null ? String(raw.collected_at) : null,
    transport_at: raw.transport_at != null ? String(raw.transport_at) : null,
    received_at: raw.received_at != null ? String(raw.received_at) : null,
    sorting_at: raw.sorting_at != null ? String(raw.sorting_at) : null,
    laboratory_at: raw.laboratory_at != null ? String(raw.laboratory_at) : null,
    completed_at: raw.completed_at != null ? String(raw.completed_at) : null,
  };
}

function mapSampleQueueDashboard(data: Record<string, unknown>): SampleQueueDashboard {
  const stats = (data.statistics as Record<string, unknown> | undefined) ?? {};
  return {
    items: Array.isArray(data.items)
      ? (data.items as Record<string, unknown>[]).map(mapSampleQueueItem)
      : [],
    statistics: {
      by_stage: (stats.by_stage as Record<string, number>) ?? {},
      total: Number(stats.total ?? 0),
      active: Number(stats.active ?? 0),
      in_transit: Number(stats.in_transit ?? 0),
      completed: Number(stats.completed ?? 0),
      pipeline: Array.isArray(stats.pipeline) ? stats.pipeline.map(String) : [],
      stages: Array.isArray(stats.stages) ? stats.stages.map(String) : [],
    },
    refreshed_at: String(data.refreshed_at ?? ""),
    version: Number(data.version ?? 0),
    changed: data.changed !== false,
    workflow: Array.isArray(data.workflow) ? data.workflow.map(String) : [],
    transitions: (data.transitions as Record<string, string[]>) ?? {},
  };
}

/** GET /api/v1/reception/workspace/sample-queue */
export async function fetchSampleQueueDashboard(
  ctx: Ctx,
  opts?: { stage?: string; version?: number; limit?: number },
): Promise<SampleQueueDashboard> {
  const params = new URLSearchParams();
  if (opts?.stage) params.set("stage", opts.stage);
  if (opts?.version != null) params.set("version", String(opts.version));
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/sample-queue${qs}`,
    requestOpts(ctx),
  );
  return mapSampleQueueDashboard(response.data ?? {});
}

/** GET /api/v1/reception/workspace/sample-queue/refresh */
export async function refreshSampleQueue(
  ctx: Ctx,
  opts?: { version?: number },
): Promise<SampleQueueDashboard> {
  const params = new URLSearchParams();
  if (opts?.version != null) params.set("version", String(opts.version));
  const qs = params.toString() ? `?${params}` : "";
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/sample-queue/refresh${qs}`,
    requestOpts(ctx),
  );
  return mapSampleQueueDashboard(response.data ?? {});
}

/** POST /api/v1/reception/workspace/sample-queue/orders/:ref/enqueue */
export async function enqueueSampleQueueOrder(
  ctx: Ctx,
  orderRef: string,
  payload?: { location?: string; note?: string },
): Promise<SampleQueueItem> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/sample-queue/orders/${encodeURIComponent(orderRef)}/enqueue`,
    requestOpts(ctx, { method: "POST", body: payload ?? {} }),
  );
  return mapSampleQueueItem(response.data ?? {});
}

/** POST /api/v1/reception/workspace/sample-queue/orders/:ref/advance */
export async function advanceSampleQueueOrder(
  ctx: Ctx,
  orderRef: string,
  to: SampleQueueStage | string,
  opts?: { note?: string; location?: string },
): Promise<SampleQueueItem> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/sample-queue/orders/${encodeURIComponent(orderRef)}/advance`,
    requestOpts(ctx, {
      method: "POST",
      body: { to, note: opts?.note, location: opts?.location },
    }),
  );
  return mapSampleQueueItem(response.data ?? {});
}

/** GET /api/v1/reception/workspace/sample-queue/orders/:ref/track */
export async function trackSampleQueueOrder(
  ctx: Ctx,
  orderRef: string,
): Promise<SampleQueueItem & { on_queue?: boolean; tracked_at?: string }> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/sample-queue/orders/${encodeURIComponent(orderRef)}/track`,
    requestOpts(ctx),
  );
  const data = response.data ?? {};
  return {
    ...mapSampleQueueItem(data),
    on_queue: Boolean(data.on_queue),
    tracked_at: data.tracked_at != null ? String(data.tracked_at) : undefined,
  };
}

/** GET /api/v1/reception/workspace/sample-queue/orders/:ref/history */
export async function fetchSampleQueueHistory(ctx: Ctx, orderRef: string) {
  const response = await apiRequest<{
    success: boolean;
    data: { history?: Record<string, unknown>[] };
  }>(
    `/api/v1/reception/workspace/sample-queue/orders/${encodeURIComponent(orderRef)}/history`,
    requestOpts(ctx),
  );
  return Array.isArray(response.data?.history)
    ? response.data!.history!.map(mapSampleQueueEvent)
    : [];
}

/** POST /api/v1/reception/workspace/sample-queue/orders/:ref/tracking */
export async function updateSampleQueueTracking(
  ctx: Ctx,
  orderRef: string,
  payload: { location?: string; note?: string },
): Promise<SampleQueueItem> {
  const response = await apiRequest<{ success: boolean; data: Record<string, unknown> }>(
    `/api/v1/reception/workspace/sample-queue/orders/${encodeURIComponent(orderRef)}/tracking`,
    requestOpts(ctx, { method: "POST", body: payload }),
  );
  return mapSampleQueueItem(response.data ?? {});
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
