import { apiRequest } from "@/services/api";

export const BOOKING_SLOTS = ["ANYTIME", "MORNING", "AFTERNOON"] as const;
export type BookingSlot = (typeof BOOKING_SLOTS)[number];

export const BOOKING_STATUSES = [
  "NEW",
  "CONTACTED",
  "SCHEDULED",
  "DONE",
  "CANCELLED",
  "SPAM",
] as const;
export type BookingStatus = (typeof BOOKING_STATUSES)[number];

export type PublicBookingBody = {
  full_name: string;
  phone: string;
  email?: string;
  address: string;
  district?: string;
  preferred_date?: string;
  preferred_slot: BookingSlot;
  note?: string;
  consent_contact: boolean;
  /** Honeypot — must stay empty for real people. */
  website?: string;
};

export type BookingRequestItem = {
  id: string;
  reference: string;
  full_name: string;
  phone: string;
  email: string | null;
  address: string;
  district: string | null;
  preferred_date: string | null;
  preferred_slot: BookingSlot;
  note: string | null;
  status: BookingStatus;
  handled_by: string | null;
  handled_at: string | null;
  internal_note: string | null;
  created_at: string | null;
  consent_at: string | null;
  consent_version: string | null;
};

type Ctx = { token: string; organizationId?: string | null };

/** Anonymous POST from the public /book page. */
export async function submitPublicBooking(body: PublicBookingBody): Promise<{ reference: string }> {
  const response = await apiRequest<{ success: boolean; data: { reference: string } }>(
    "/api/v1/public/bookings",
    { method: "POST", body, timeoutMs: 30_000 },
  );
  return response.data;
}

export async function listBookingRequests(
  ctx: Ctx,
  status?: BookingStatus,
): Promise<{ items: BookingRequestItem[]; new_count: number }> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await apiRequest<{
    success: boolean;
    data: { items: BookingRequestItem[]; new_count: number };
  }>(`/api/v1/reception/workspace/booking-requests${query}`, {
    token: ctx.token,
    organizationId: ctx.organizationId ?? null,
    timeoutMs: 30_000,
  });
  return response.data;
}

export async function setBookingStatus(
  ctx: Ctx,
  id: string,
  status: BookingStatus,
  internalNote?: string,
): Promise<BookingRequestItem> {
  const response = await apiRequest<{ success: boolean; data: BookingRequestItem }>(
    `/api/v1/reception/workspace/booking-requests/${encodeURIComponent(id)}/status`,
    {
      method: "POST",
      token: ctx.token,
      organizationId: ctx.organizationId ?? null,
      body: { status, internal_note: internalNote },
      timeoutMs: 30_000,
    },
  );
  return response.data;
}
