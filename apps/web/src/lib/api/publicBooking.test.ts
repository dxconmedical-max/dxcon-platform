import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import { listBookingRequests, setBookingStatus, submitPublicBooking } from "./publicBooking";

const ctx = { token: "t", organizationId: "org-1" };

describe("public booking API client", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("submits anonymously (no token) to the public endpoint", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: { reference: "BK-1" } });
    const result = await submitPublicBooking({
      full_name: "A",
      phone: "0901234567",
      address: "12 Test St",
      preferred_slot: "ANYTIME",
      consent_contact: true,
    });
    expect(result.reference).toBe("BK-1");
    const [path, options] = vi.mocked(apiRequest).mock.calls[0];
    expect(path).toBe("/api/v1/public/bookings");
    expect(options).toEqual(expect.objectContaining({ method: "POST" }));
    expect(options).not.toHaveProperty("token");
  });

  it("lists with an optional status filter", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: { items: [], new_count: 0 } });
    await listBookingRequests(ctx, "NEW");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/booking-requests?status=NEW",
      expect.objectContaining({ token: "t", organizationId: "org-1" }),
    );
  });

  it("updates status with a note", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: { id: "x", status: "CONTACTED" } });
    await setBookingStatus(ctx, "x/1", "CONTACTED", "called");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/booking-requests/x%2F1/status",
      expect.objectContaining({
        method: "POST",
        body: { status: "CONTACTED", internal_note: "called" },
      }),
    );
  });
});
