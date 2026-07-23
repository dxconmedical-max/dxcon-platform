import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import {
  fetchReceptionLabHandoff,
  handoffReceptionOrderToLab,
  RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
} from "./reception";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception Milestone 4 lab handoff API", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("posts handoff with timeout and maps payload", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order_code: "ORD-1",
        order_status: "lab_received",
        collection: { status: "delivered" },
        queue_reference: "ACC-9",
        laboratory: { id: "lab-1", name: "Central Laboratory" },
        accepted_at: "2026-07-24T02:00:00Z",
        handed_off: true,
        idempotent_replay: false,
      },
    });
    const result = await handoffReceptionOrderToLab(ctx, "ORD-1");
    expect(result.order_status).toBe("lab_received");
    expect(result.queue_reference).toBe("ACC-9");
    expect(result.handed_off).toBe(true);
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/orders/ORD-1/lab-handoff",
      expect.objectContaining({
        method: "POST",
        timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
      }),
    );
  });

  it("normalizes handoff errors", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Order must be paid before laboratory handoff", 400, {
        error: "Order must be paid before laboratory handoff",
      }),
    );
    await expect(handoffReceptionOrderToLab(ctx, "ORD-1")).rejects.toMatchObject({
      status: 400,
      message: "Order must be paid before laboratory handoff",
    });
  });

  it("fetches handoff status for refresh persistence", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order_code: "ORD-1",
        order_status: "lab_received",
        queue_reference: "ACC-9",
        laboratory: { name: "Central Laboratory" },
        handed_off: true,
        idempotent_replay: true,
      },
    });
    const status = await fetchReceptionLabHandoff(ctx, "ORD-1");
    expect(status.handed_off).toBe(true);
    expect(status.idempotent_replay).toBe(true);
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/orders/ORD-1/lab-handoff",
      expect.objectContaining({ timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS }),
    );
  });
});
