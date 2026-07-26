import { apiRequest } from "@/services/api";
import { ApiError } from "@/lib/errors";

export type SampleCollectionAuth = {
  token?: string | null;
  organizationId?: string | null;
  collectorId?: string | null;
  partnerId?: string | null;
};

export type SampleCollectionItem = {
  id: string;
  source?: "field" | "desk" | string;
  status: string;
  order_id?: string;
  marketplace_booking_id?: string | null;
  collector_id?: string | null;
  collector_name?: string | null;
  specimen_type?: string | null;
  barcode_value?: string | null;
  expected_barcode?: string | null;
  collection_location?: string | null;
  location_city?: string | null;
  quality_status?: string | null;
  rejection_reason?: string | null;
  collected_at?: string | null;
  picked_up_at?: string | null;
  dispatched_at?: string | null;
  handoff_at?: string | null;
  arrived_at_lab?: string | null;
  vehicle_id?: string | null;
  driver_id?: string | null;
  transport_box_id?: string | null;
  distance_km?: number | null;
  eta_minutes?: number | null;
  temperature_c?: number | null;
  sample_tracking?: {
    id?: string;
    sample_code?: string;
    status?: string;
  } | null;
  booking?: {
    id?: string;
    booking_code?: string;
    patient_name?: string;
    patient_phone?: string;
    patient_address?: string;
    city?: string;
    partner_id?: string;
  } | null;
  order?: Record<string, unknown> | null;
  sample_code?: string;
  pickup_address?: string;
  [key: string]: unknown;
};

export type SampleCollectionQueue = {
  count: number;
  items: SampleCollectionItem[];
  field_count: number;
  desk_count: number;
};

export type SampleCollectionDashboard = {
  kpis: {
    awaiting_collection: number;
    in_transit: number;
    arrived_at_lab: number;
    rejected: number;
    desk_jobs_awaiting: number;
  };
  status_contract: {
    queue: string[];
    flow: string[];
    exceptions: string[];
  };
};

function authHeaders(auth: SampleCollectionAuth): Record<string, string> {
  const headers: Record<string, string> = {};
  if (auth.collectorId) headers["X-Collector-Id"] = auth.collectorId;
  if (auth.partnerId) headers["X-Partner-Id"] = auth.partnerId;
  return headers;
}

function opts(auth: SampleCollectionAuth, extra?: { timeoutMs?: number; signal?: AbortSignal }) {
  return {
    token: auth.token,
    organizationId: auth.organizationId,
    headers: authHeaders(auth),
    timeoutMs: extra?.timeoutMs,
    signal: extra?.signal,
  };
}

async function unwrap<T>(promise: Promise<{ success?: boolean; data?: T; error?: string }>): Promise<T> {
  const body = await promise;
  if (body && body.success === false) {
    throw new ApiError(body.error || "Sample collection request failed", 400);
  }
  if (body && "data" in body) {
    return body.data as T;
  }
  return body as unknown as T;
}

export async function fetchCollectionDashboard(auth: SampleCollectionAuth) {
  return unwrap(
    apiRequest<{ success: boolean; data: SampleCollectionDashboard }>(
      "/api/v1/sample-collections/dashboard",
      { method: "GET", ...opts(auth) },
    ),
  );
}

export async function fetchCollectionQueue(
  auth: SampleCollectionAuth,
  filters: {
    status?: string;
    collector?: string;
    location?: string;
    date?: string;
    date_to?: string;
    include_desk?: boolean;
  } = {},
  extra?: { timeoutMs?: number; signal?: AbortSignal },
) {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.collector) params.set("collector", filters.collector);
  if (filters.location) params.set("location", filters.location);
  if (filters.date) params.set("date", filters.date);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.include_desk === false) params.set("include_desk", "false");
  const qs = params.toString();
  return unwrap(
    apiRequest<{ success: boolean; data: SampleCollectionQueue }>(
      `/api/v1/sample-collections/queue${qs ? `?${qs}` : ""}`,
      { method: "GET", ...opts(auth, extra) },
    ),
  );
}

export async function fetchCollection(auth: SampleCollectionAuth, collectionId: string) {
  return unwrap(
    apiRequest<{ success: boolean; data: SampleCollectionItem }>(
      `/api/v1/sample-collections/${encodeURIComponent(collectionId)}`,
      { method: "GET", ...opts(auth) },
    ),
  );
}

export async function verifyCollection(
  auth: SampleCollectionAuth,
  collectionId: string,
  body: {
    patient_name?: string;
    booking_code?: string;
    order_id?: string;
    scanned_barcode?: string;
  },
) {
  return unwrap(
    apiRequest<{ success: boolean; data: SampleCollectionItem }>(
      `/api/v1/sample-collections/${encodeURIComponent(collectionId)}/verify`,
      { method: "POST", body, ...opts(auth) },
    ),
  );
}

export async function collectSpecimen(
  auth: SampleCollectionAuth,
  collectionId: string,
  body: {
    scanned_barcode: string;
    specimen_type?: string;
    collector_id?: string;
    collection_location?: string;
    notes?: string;
    latitude?: string;
    longitude?: string;
    require_barcode?: boolean;
    patient_verified?: boolean;
    order_verified?: boolean;
  },
) {
  return unwrap(
    apiRequest<{
      success: boolean;
      data: { collection: SampleCollectionItem; sample_tracking: Record<string, unknown> };
    }>(`/api/v1/sample-collections/${encodeURIComponent(collectionId)}/collect`, {
      method: "POST",
      body,
      ...opts(auth),
    }),
  );
}

export async function rejectSpecimen(
  auth: SampleCollectionAuth,
  collectionId: string,
  body: {
    quality_status: string;
    rejection_reason?: string;
    request_recollect?: boolean;
  },
) {
  return unwrap(
    apiRequest<{
      success: boolean;
      data: { collection: SampleCollectionItem; recollect: SampleCollectionItem | null };
    }>(`/api/v1/sample-collections/${encodeURIComponent(collectionId)}/reject`, {
      method: "POST",
      body,
      ...opts(auth),
    }),
  );
}

export async function dispatchCollection(
  auth: SampleCollectionAuth,
  bookingId: string,
  body: {
    transport_box_id?: string;
    vehicle_id?: string;
    driver_id?: string;
    distance_km?: number;
    eta_minutes?: number;
    temperature_c?: number;
    iot_device_id?: string;
    note?: string;
  } = {},
) {
  return unwrap(
    apiRequest<{
      success: boolean;
      data: { collection: SampleCollectionItem; sample_tracking: Record<string, unknown> };
    }>(`/api/v1/sample-collections/bookings/${encodeURIComponent(bookingId)}/dispatch`, {
      method: "POST",
      body,
      ...opts(auth),
    }),
  );
}

export async function handoffCollection(
  auth: SampleCollectionAuth,
  collectionId: string,
  body: { note?: string; temperature_c?: number } = {},
) {
  return unwrap(
    apiRequest<{ success: boolean; data: SampleCollectionItem }>(
      `/api/v1/sample-collections/${encodeURIComponent(collectionId)}/handoff`,
      { method: "POST", body, ...opts(auth) },
    ),
  );
}

export async function arriveAtLab(
  auth: SampleCollectionAuth,
  bookingId: string,
  body: { note?: string; temperature_c?: number } = {},
) {
  return unwrap(
    apiRequest<{
      success: boolean;
      data: {
        collection: SampleCollectionItem;
        sample_tracking: Record<string, unknown>;
        synthetic_specimen_id?: string;
      };
    }>(`/api/v1/sample-collections/bookings/${encodeURIComponent(bookingId)}/lab-arrive`, {
      method: "POST",
      body,
      ...opts(auth),
    }),
  );
}

export async function fetchTransportStatus(auth: SampleCollectionAuth, collectionId: string) {
  return unwrap(
    apiRequest<{ success: boolean; data: Record<string, unknown> }>(
      `/api/v1/sample-collections/${encodeURIComponent(collectionId)}/transport`,
      { method: "GET", ...opts(auth) },
    ),
  );
}

export const QUALITY_REJECTION_OPTIONS = [
  { value: "insufficient_volume", label: "Insufficient volume" },
  { value: "wrong_tube", label: "Wrong tube" },
  { value: "hemolyzed", label: "Hemolysis" },
  { value: "contaminated", label: "Contamination" },
  { value: "mismatched_identifier", label: "Mismatched identifier" },
  { value: "rejected", label: "Rejected (other)" },
] as const;
