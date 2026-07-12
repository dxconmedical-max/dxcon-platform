import { apiRequest } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";
import {
  SAMPLE_CATALOG,
  SAMPLE_LOCATIONS,
  sampleSlots,
} from "./samples";

export type CatalogItem = {
  code: string;
  name: string;
  category?: string;
  sample_type?: string;
  price?: number;
  turnaround_hours?: number;
  home_collection?: boolean;
};

export type ServiceLocation = {
  id: string;
  name: string;
  city?: string;
  address?: string;
  home_collection?: boolean;
};

export type TimeSlot = {
  id: string;
  date: string;
  time: string;
  capacity: number;
  booked: number;
  available: boolean;
};

export type BookingDraft = {
  items: CatalogItem[];
  locationId: string | null;
  homeCollection: boolean;
  homeAddress?: string;
  slot: TimeSlot | null;
  contactName?: string;
  contactPhone?: string;
};

export type BookingConfirmation = {
  reference: string;
  qrPayload: string;
  scheduled_at: string;
  location: string;
  total: number;
  status: string;
};

type Ctx = { token: string; organizationId: string };

/** Package / test catalog. Backed by GET /api/v1/test-catalogs (live). */
export async function fetchCatalog(
  { token, organizationId }: Ctx,
  query?: string,
): Promise<Sourced<CatalogItem[]>> {
  return withSampleFallback<CatalogItem[]>(
    async () => {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      const suffix = params.toString() ? `?${params}` : "";
      const response = await apiRequest<{ count?: number; data?: unknown }>(
        `/api/v1/test-catalogs${suffix}`,
        { token, organizationId },
      );
      const raw = Array.isArray(response.data) ? response.data : [];
      const items = raw.map((row) => {
        const record = row as Record<string, unknown>;
        return {
          code: String(record.code ?? record.id ?? ""),
          name: String(record.name ?? record.code ?? "Unnamed test"),
          category: record.category ? String(record.category) : undefined,
          sample_type: record.sample_type ? String(record.sample_type) : undefined,
          price: typeof record.price === "number" ? record.price : Number(record.price) || undefined,
          turnaround_hours:
            typeof record.turnaround_hours === "number" ? record.turnaround_hours : undefined,
          home_collection: Boolean(record.home_collection ?? true),
        } satisfies CatalogItem;
      });
      if (items.length === 0) throw new Error("empty catalog");
      return items;
    },
    SAMPLE_CATALOG,
    SAMPLE_NOTE,
  );
}

/**
 * Service locations / branches. No dedicated backend list endpoint exists yet,
 * so this is a labeled sample adapter.
 */
export async function fetchLocations(_ctx: Ctx): Promise<Sourced<ServiceLocation[]>> {
  void _ctx;
  return { value: SAMPLE_LOCATIONS, source: "sample", note: SAMPLE_NOTE };
}

/**
 * Available time slots for a location/date. Attempts the scheduling API and
 * falls back to a labeled sample schedule when unavailable.
 */
export async function fetchSlots(
  { token, organizationId }: Ctx,
  locationId: string,
  dateISO: string,
): Promise<Sourced<TimeSlot[]>> {
  return withSampleFallback<TimeSlot[]>(
    async () => {
      const params = new URLSearchParams({ date: dateISO });
      const response = await apiRequest<{ count?: number; slots?: unknown }>(
        `/api/v1/scheduling/partners/${encodeURIComponent(locationId)}/slots?${params}`,
        { token, organizationId },
      );
      const raw = Array.isArray(response.slots) ? response.slots : [];
      const slots = raw.map((row) => {
        const record = row as Record<string, unknown>;
        const capacity = Number(record.capacity ?? record.slot_capacity ?? 0);
        const booked = Number(record.booked ?? record.reserved ?? 0);
        return {
          id: String(record.id ?? record.slot_id ?? `${dateISO}-${record.time ?? ""}`),
          date: dateISO,
          time: String(record.time ?? record.start_time ?? ""),
          capacity,
          booked,
          available: capacity === 0 ? true : booked < capacity,
        } satisfies TimeSlot;
      });
      if (slots.length === 0) throw new Error("no slots");
      return slots;
    },
    sampleSlots(dateISO),
    SAMPLE_NOTE,
  );
}

/**
 * Create a booking and return a QR confirmation. Attempts the marketplace v2
 * booking API; falls back to a labeled sample confirmation when unavailable.
 */
export async function createBooking(
  { token, organizationId }: Ctx,
  draft: BookingDraft,
): Promise<Sourced<BookingConfirmation>> {
  const total = draft.items.reduce((sum, item) => sum + (item.price ?? 0), 0);
  const locationLabel = draft.homeCollection
    ? `Home collection${draft.homeAddress ? ` — ${draft.homeAddress}` : ""}`
    : draft.locationId ?? "Selected location";
  const scheduledAt = draft.slot ? `${draft.slot.date} ${draft.slot.time}` : "To be scheduled";

  return withSampleFallback<BookingConfirmation>(
    async () => {
      const response = await apiRequest<{ booking?: Record<string, unknown>; data?: Record<string, unknown> }>(
        "/api/v1/marketplace/v2/bookings",
        {
          token,
          organizationId,
          method: "POST",
          headers: organizationId ? { "X-Organization-Id": organizationId } : {},
          body: {
            test_codes: draft.items.map((item) => item.code),
            location_id: draft.locationId,
            home_collection: draft.homeCollection,
            home_address: draft.homeAddress,
            slot_id: draft.slot?.id,
            contact_name: draft.contactName,
            contact_phone: draft.contactPhone,
          },
        },
      );
      const booking = (response.booking ?? response.data ?? {}) as Record<string, unknown>;
      const reference = String(booking.reference ?? booking.booking_reference ?? booking.id ?? "");
      if (!reference) throw new Error("no booking reference");
      return {
        reference,
        qrPayload: String(booking.qr_payload ?? booking.qr ?? reference),
        scheduled_at: String(booking.scheduled_at ?? scheduledAt),
        location: String(booking.location ?? locationLabel),
        total: typeof booking.total_amount === "number" ? booking.total_amount : total,
        status: String(booking.status ?? "CONFIRMED"),
      };
    },
    {
      reference: `BKG-${Math.floor(100000 + Math.random() * 899999)}`,
      qrPayload: `DXCON|BOOKING|${scheduledAt}|${total}`,
      scheduled_at: scheduledAt,
      location: locationLabel,
      total,
      status: "CONFIRMED",
    },
    SAMPLE_NOTE,
  );
}
