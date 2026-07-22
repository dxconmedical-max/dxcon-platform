import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("./client", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "./client";
import {
  createReceptionOrder,
  fetchReceptionTests,
  getOrderCode,
  registerWalkIn,
  searchReceptionPatients,
} from "./reception";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception Milestone 1 API client", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("searches patients from the live reception workspace endpoint", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: [
        {
          patient_code: "P-100",
          full_name: "Jane Doe",
          phone: "0901",
          national_id: "NID1",
        },
      ],
      pagination: { total: 1 },
    });

    const result = await searchReceptionPatients(ctx, "Jane");
    expect(result.items).toHaveLength(1);
    expect(result.items[0].patient_code).toBe("P-100");
    expect(apiRequest).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/reception/workspace/search?"),
      expect.objectContaining({ token: "t", organizationId: "org-1" }),
    );
  });

  it("registers a patient without sample fallback", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        patient: { patient_code: "P-200", full_name: "New Patient" },
        message: "Patient registered.",
      },
    });
    const result = await registerWalkIn(ctx, { full_name: "New Patient", phone: "0907111222" });
    expect(result.value.patient_code).toBe("P-200");
    expect(result.source).toBe("live");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/patients/register",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("loads tests and creates an order", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({
        success: true,
        data: [{ id: "t1", code: "CBC", name: "Complete Blood Count", price: 150000 }],
        pagination: { total: 1 },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          order: { order_code: "ORD-1", status: "payment_pending" },
          invoice: { id: "inv-1" },
          pricing: { subtotal: 150000, discount: 0, total: 150000 },
        },
      });

    const tests = await fetchReceptionTests(ctx);
    const order = await createReceptionOrder(ctx, {
      patient_code: "P-100",
      test_catalog_ids: ["t1"],
    });

    expect(tests.items[0].code).toBe("CBC");
    expect(getOrderCode(order.order)).toBe("ORD-1");
    expect(order.pricing.total).toBe(150000);

    const paths = vi.mocked(apiRequest).mock.calls.map((call) => call[0] as string);
    expect(paths[0]).toContain("/api/v1/reception/workspace/tests?");
    expect(paths[1]).toBe("/api/v1/reception/workspace/orders");
  });

  it("surfaces API failures instead of swallowing them", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error("Request failed (403)"));
    await expect(fetchReceptionTests(ctx)).rejects.toThrow(/403|failed/i);
  });
});
