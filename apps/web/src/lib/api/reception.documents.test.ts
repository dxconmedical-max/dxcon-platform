import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import {
  fetchReceptionBarcodes,
  fetchReceptionRequestForm,
  isValidPatientQr,
} from "./reception";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception Milestone 3 barcode/QR/requisition API", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("generates identifiers", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order_barcode: "BC-ORD-1",
        patient_barcode: "BC-PAT-P1",
        patient_qr: "dxcon:patient:P1",
        sample_barcodes: [
          {
            test_code: "CBC",
            test_name: "CBC",
            specimen_code: "SMP-CBC-ORD-1",
            barcode: "BC-SMP-CBC-ORD-1",
          },
        ],
        reprint: false,
        generated_at: "2026-07-24T00:00:00Z",
      },
    });
    const result = await fetchReceptionBarcodes(ctx, "ORD-1");
    expect(result.order_barcode).toBe("BC-ORD-1");
    expect(isValidPatientQr(result.patient_qr)).toBe(true);
    expect(result.sample_barcodes[0].barcode).toBe("BC-SMP-CBC-ORD-1");
  });

  it("retrieves existing / reprint flag", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order_barcode: "BC-ORD-1",
        patient_barcode: "BC-PAT-P1",
        patient_qr: "dxcon:patient:P1",
        sample_barcodes: [],
        reprint: true,
      },
    });
    const result = await fetchReceptionBarcodes(ctx, "ORD-1");
    expect(result.reprint).toBe(true);
  });

  it("QR payload validity helper", () => {
    expect(isValidPatientQr("dxcon:patient:P-1")).toBe(true);
    expect(isValidPatientQr("bad")).toBe(false);
  });

  it("invalid order status", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Order must be paid before barcode, QR, or requisition generation", 400, {
        error: "Order must be paid before barcode, QR, or requisition generation",
      }),
    );
    await expect(fetchReceptionBarcodes(ctx, "ORD-UNPAID")).rejects.toMatchObject({
      status: 400,
    });
  });

  it("permission denial", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Forbidden", 403, { error: "Forbidden" }),
    );
    await expect(fetchReceptionRequestForm(ctx, "ORD-1")).rejects.toMatchObject({
      status: 403,
    });
  });

  it("requisition content", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        html: "<html><body>Lab Request Form ORD-1</body></html>",
        order_code: "ORD-1",
        barcodes: {
          order_barcode: "BC-ORD-1",
          patient_barcode: "BC-PAT-P1",
          patient_qr: "dxcon:patient:P1",
          sample_barcodes: [],
        },
      },
    });
    const form = await fetchReceptionRequestForm(ctx, "ORD-1");
    expect(form.html).toContain("Lab Request Form");
    expect(form.barcodes?.order_barcode).toBe("BC-ORD-1");
  });

  it("happy path barcode then requisition", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({
        success: true,
        data: {
          order_barcode: "BC-ORD-H",
          patient_barcode: "BC-PAT-P",
          patient_qr: "dxcon:patient:P",
          sample_barcodes: [{ test_code: "CBC", test_name: "CBC", barcode: "BC-S" }],
          reprint: false,
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          html: "<html>req</html>",
          barcodes: {
            order_barcode: "BC-ORD-H",
            patient_barcode: "BC-PAT-P",
            patient_qr: "dxcon:patient:P",
            sample_barcodes: [],
            reprint: true,
          },
          reprint: true,
        },
      });
    const codes = await fetchReceptionBarcodes(ctx, "ORD-H");
    const form = await fetchReceptionRequestForm(ctx, "ORD-H");
    expect(codes.order_barcode).toBe("BC-ORD-H");
    expect(form.reprint).toBe(true);
  });
});
