import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import {
  catalogCategories,
  createReceptionOrder,
  fetchReceptionOrder,
  fetchReceptionPatient,
  fetchReceptionTests,
  getDuplicateWarnings,
  getOrderCode,
  registerWalkIn,
  searchReceptionPatients,
} from "./reception";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception Milestone 1 API client", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("1. patient search success", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: [{ patient_code: "P-100", full_name: "Jane Doe", phone: "0901" }],
      pagination: { total: 1 },
    });
    const result = await searchReceptionPatients(ctx, "Jane");
    expect(result.items[0].patient_code).toBe("P-100");
    expect(apiRequest).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/reception/workspace/search?"),
      expect.objectContaining({ token: "t", organizationId: "org-1" }),
    );
  });

  it("2. patient search empty", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: [],
      pagination: { total: 0 },
    });
    const result = await searchReceptionPatients(ctx, "zzz-none");
    expect(result.items).toEqual([]);
    expect(result.total).toBe(0);
  });

  it("3. patient search failure", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new ApiError("Forbidden", 403, { error: "Forbidden" }));
    await expect(searchReceptionPatients(ctx, "x")).rejects.toMatchObject({ status: 403 });
  });

  it("4. patient creation", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        patient: { patient_code: "P-200", full_name: "New Patient", phone: "0907111222" },
      },
    });
    const result = await registerWalkIn(ctx, { full_name: "New Patient", phone: "0907111222" });
    expect(result.patient_code).toBe("P-200");
  });

  it("5. validation failure", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("full_name is required", 400, { error: "full_name is required" }),
    );
    await expect(registerWalkIn(ctx, { full_name: "", phone: "1" })).rejects.toMatchObject({
      status: 400,
    });
  });

  it("6. duplicate detection", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("duplicate", 409, {
        success: false,
        duplicate: true,
        warnings: [{ field: "phone", message: "Phone already registered", patient_code: "P-1" }],
      }),
    );
    try {
      await registerWalkIn(ctx, { full_name: "Dup", phone: "0901" });
      throw new Error("expected throw");
    } catch (error) {
      expect(getDuplicateWarnings(error)[0]?.patient_code).toBe("P-1");
    }
  });

  it("7. catalog search", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: [
        {
          id: "t1",
          code: "CBC",
          name: "Complete Blood Count",
          price: 150000,
          sample_type: "Blood",
          category: "Hematology",
        },
      ],
      pagination: { total: 1 },
    });
    const tests = await fetchReceptionTests(ctx, { q: "CBC" });
    expect(tests.items[0].sample_type).toBe("Blood");
    expect(String(vi.mocked(apiRequest).mock.calls[0]?.[0])).toContain("q=CBC");
  });

  it("8. package selection categories", () => {
    expect(
      catalogCategories([
        { id: "1", code: "A", name: "A", category: "Hematology" },
        { id: "2", code: "B", name: "B", category: "Hematology" },
        { id: "3", code: "C", name: "C", category: "Chemistry" },
      ]),
    ).toEqual(["Chemistry", "Hematology"]);
  });

  it("9-10. add/remove and duplicate test prevention via unique ids in create payload", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order: { order_code: "ORD-1", items: [{ test_code: "CBC" }] },
        invoice: { id: "inv-1" },
        pricing: { subtotal: 150000, discount: 0, total: 150000 },
      },
    });
    await createReceptionOrder(ctx, {
      patient_code: "P-100",
      test_catalog_ids: ["t1", "t1", "t1"],
    });
    const body = (vi.mocked(apiRequest).mock.calls[0]?.[1] as { body: { test_catalog_ids: string[] } })
      .body;
    expect(body.test_catalog_ids).toEqual(["t1"]);
  });

  it("11. authoritative pricing from backend", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order: { order_code: "ORD-1" },
        invoice: {},
        pricing: { subtotal: 200000, discount: 20000, total: 180000 },
      },
    });
    const order = await createReceptionOrder(ctx, {
      patient_code: "P-100",
      test_catalog_ids: ["t1"],
      discount: 20000,
    });
    expect(order.pricing).toEqual({
      subtotal: 200000,
      discount: 20000,
      total: 180000,
      tax: null,
    });
  });

  it("12. order creation", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order: { order_code: "ORD-9", status: "payment_pending" },
        invoice: { id: "inv-9" },
        pricing: { subtotal: 1, discount: 0, total: 1 },
      },
    });
    const order = await createReceptionOrder(ctx, {
      patient_code: "P-100",
      test_catalog_ids: ["t1"],
    });
    expect(getOrderCode(order.order)).toBe("ORD-9");
  });

  it("13. duplicate order submission prevention is UI-level; API still surfaces 400 on failure", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("At least one test is required", 400, {
        error: "At least one test is required",
      }),
    );
    await expect(
      createReceptionOrder(ctx, { patient_code: "P-100", test_catalog_ids: [] }),
    ).rejects.toMatchObject({ status: 400 });
  });

  it("14. partial failure handling", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Patient not found", 400, { error: "Patient not found" }),
    );
    await expect(
      createReceptionOrder(ctx, { patient_code: "missing", test_catalog_ids: ["t1"] }),
    ).rejects.toMatchObject({ status: 400 });
  });

  it("15. refresh persistence via fetch order + patient", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({
        success: true,
        data: {
          order: { order_code: "ORD-1", patient_code: "P-100", status: "payment_pending" },
          pricing: { subtotal: 10, discount: 0, total: 10 },
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: { patient_code: "P-100", full_name: "Jane", orders: [{ order_code: "ORD-1" }] },
      });
    const order = await fetchReceptionOrder(ctx, "ORD-1");
    const patient = await fetchReceptionPatient(ctx, "P-100");
    expect(order.pricing.total).toBe(10);
    expect(patient.orders?.[0]?.order_code).toBe("ORD-1");
  });

  it("16. permission denial", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Forbidden", 403, { error: "Forbidden" }),
    );
    await expect(fetchReceptionTests(ctx)).rejects.toMatchObject({ status: 403 });
  });

  it("17. complete patient-to-order happy path", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({
        success: true,
        data: [{ patient_code: "P-100", full_name: "Jane" }],
        pagination: { total: 1 },
      })
      .mockResolvedValueOnce({
        success: true,
        data: [{ id: "t1", code: "CBC", name: "CBC", price: 150000, category: "Hematology" }],
        pagination: { total: 1 },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          order: { order_code: "ORD-HAPPY", patient_code: "P-100", items: [{ test_code: "CBC" }] },
          invoice: { id: "inv" },
          pricing: { subtotal: 150000, discount: 0, total: 150000 },
        },
      });

    const patients = await searchReceptionPatients(ctx, "Jane");
    const tests = await fetchReceptionTests(ctx, { q: "CBC" });
    const order = await createReceptionOrder(ctx, {
      patient_code: patients.items[0].patient_code,
      test_catalog_ids: [tests.items[0].id],
    });
    expect(getOrderCode(order.order)).toBe("ORD-HAPPY");
    expect(order.pricing.total).toBe(150000);
  });

  it("passes AbortSignal through search", async () => {
    const controller = new AbortController();
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: [], pagination: { total: 0 } });
    await searchReceptionPatients({ ...ctx, signal: controller.signal }, "a");
    expect(apiRequest).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ signal: controller.signal }),
    );
  });
});
