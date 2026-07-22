import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("./client", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "./client";
import {
  createPatient,
  createOrder,
  payOrder,
  scheduleCollection,
  collectSample,
  markInTransit,
  receiveAtLab,
  enterResults,
  completeQc,
  approveResult,
  releaseResult,
  fetchReport,
} from "./diagnostic-workflow";

const ctx = { token: "t", organizationId: "org-1" };

describe("diagnostic-workflow API client", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("posts create patient to the live workflow endpoint", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: { patient_code: "P-1", full_name: "A" },
    });
    const patient = await createPatient(ctx, { full_name: "A", phone: "0901" });
    expect(patient.patient_code).toBe("P-1");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/diagnostic-workflow/patients",
      expect.objectContaining({ method: "POST", token: "t", organizationId: "org-1" }),
    );
  });

  it("chains order lifecycle paths without sample fallbacks", async () => {
    const order = { order_code: "O-1", status: "paid", milestone: "ORDERED" };
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: order });

    await createOrder(ctx, { patient_code: "P-1", test_catalog_ids: ["t1"] });
    await payOrder(ctx, "O-1");
    await scheduleCollection(ctx, "O-1");
    await collectSample(ctx, "O-1");
    await markInTransit(ctx, "O-1");
    await receiveAtLab(ctx, "O-1");
    await enterResults(ctx, "O-1");
    await completeQc(ctx, "O-1");
    await approveResult(ctx, "O-1");
    await releaseResult(ctx, "O-1");

    const paths = vi.mocked(apiRequest).mock.calls.map((c) => c[0] as string);
    expect(paths).toEqual([
      "/api/v1/diagnostic-workflow/orders",
      "/api/v1/diagnostic-workflow/orders/O-1/pay",
      "/api/v1/diagnostic-workflow/orders/O-1/collection",
      "/api/v1/diagnostic-workflow/orders/O-1/collect",
      "/api/v1/diagnostic-workflow/orders/O-1/transit",
      "/api/v1/diagnostic-workflow/orders/O-1/receive",
      "/api/v1/diagnostic-workflow/orders/O-1/results",
      "/api/v1/diagnostic-workflow/orders/O-1/qc",
      "/api/v1/diagnostic-workflow/orders/O-1/approve",
      "/api/v1/diagnostic-workflow/orders/O-1/release",
    ]);
  });

  it("surfaces API failures instead of swallowing them", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error("Request failed (409)"));
    await expect(createPatient(ctx, { full_name: "Dup", phone: "0901" })).rejects.toThrow(
      /409|failed/i,
    );
  });

  it("fetches released report HTML", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: { html: "<html>ok</html>", filename: "O-1-report.html" },
    });
    const report = await fetchReport(ctx, "O-1");
    expect(report.html).toContain("ok");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/diagnostic-workflow/orders/O-1/report",
      expect.objectContaining({ token: "t" }),
    );
  });
});
