import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import {
  collectReceptionPayment,
  createReceptionOrder,
  fetchReceptionBarcodes,
  fetchReceptionRequestForm,
  fetchReceptionTests,
  getDuplicateWarnings,
  getOrderCode,
  registerWalkIn,
  searchReceptionPatients,
} from "./reception";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception production API client", () => {
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

  it("registers a patient and returns persisted codes", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        patient: { patient_code: "P-200", full_name: "New Patient", qr_payload: "dxcon:patient:P-200" },
        qr_payload: "dxcon:patient:P-200",
      },
    });
    const result = await registerWalkIn(ctx, { full_name: "New Patient", phone: "0907111222" });
    expect(result.patient_code).toBe("P-200");
    expect(result.qr_payload).toBe("dxcon:patient:P-200");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/patients/register",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("surfaces duplicate detection from 409 responses", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("duplicate", 409, {
        success: false,
        duplicate: true,
        warnings: [{ field: "phone", message: "Phone already registered", patient_code: "P-1" }],
      }),
    );

    await expect(
      registerWalkIn(ctx, { full_name: "Dup", phone: "0901" }),
    ).rejects.toMatchObject({ status: 409 });

    try {
      await registerWalkIn(ctx, { full_name: "Dup", phone: "0901", force: false });
    } catch (error) {
      const warnings = getDuplicateWarnings(error);
      expect(warnings[0]?.patient_code).toBe("P-1");
    }
  });

  it("loads tests, creates an order, collects payment, and fetches documents", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({
        success: true,
        data: [{ id: "t1", code: "CBC", name: "Complete Blood Count", price: 150000, category: "Hematology" }],
        pagination: { total: 1 },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          order: { order_code: "ORD-1", status: "payment_pending" },
          invoice: { id: "inv-1" },
          pricing: { subtotal: 150000, discount: 10000, total: 140000 },
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          payment: { receipt_number: "R-1" },
          invoice: { id: "inv-1", status: "paid" },
          order_status: "paid",
          barcodes: {
            order_barcode: "BC-ORD-1",
            patient_barcode: "BC-PAT-P-100",
            patient_qr: "dxcon:patient:P-100",
            sample_barcodes: [{ test_code: "CBC", test_name: "Complete Blood Count", barcode: "BC-SMP-CBC" }],
          },
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          order_barcode: "BC-ORD-1",
          patient_qr: "dxcon:patient:P-100",
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: { html: "<html><body>requisition</body></html>" },
      });

    const tests = await fetchReceptionTests(ctx, { q: "CBC", category: "Hematology" });
    const order = await createReceptionOrder(ctx, {
      patient_code: "P-100",
      test_catalog_ids: ["t1"],
      discount: 10000,
    });
    const payment = await collectReceptionPayment(ctx, "ORD-1", { payment_method: "cash" });
    const barcodes = await fetchReceptionBarcodes(ctx, "ORD-1");
    const form = await fetchReceptionRequestForm(ctx, "ORD-1");

    expect(tests.items[0].code).toBe("CBC");
    expect(getOrderCode(order.order)).toBe("ORD-1");
    expect(order.pricing.total).toBe(140000);
    expect(payment.order_status).toBe("paid");
    expect(payment.barcodes.order_barcode).toBe("BC-ORD-1");
    expect(barcodes.patient_qr).toBe("dxcon:patient:P-100");
    expect(form.html).toContain("requisition");

    const paths = vi.mocked(apiRequest).mock.calls.map((call) => call[0] as string);
    expect(paths[0]).toContain("/api/v1/reception/workspace/tests?");
    expect(paths[0]).toContain("q=CBC");
    expect(paths[1]).toBe("/api/v1/reception/workspace/orders");
    expect(paths[2]).toBe("/api/v1/reception/workspace/orders/ORD-1/payment");
    expect(paths[3]).toBe("/api/v1/reception/workspace/orders/ORD-1/barcode");
    expect(paths[4]).toBe("/api/v1/reception/workspace/orders/ORD-1/request-form");
  });

  it("surfaces API failures instead of swallowing them", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error("Request failed (403)"));
    await expect(fetchReceptionTests(ctx)).rejects.toThrow(/403|failed/i);
  });
});
