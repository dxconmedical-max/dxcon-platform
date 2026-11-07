import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import { getClinicReport, listClinicReports } from "./clinicResults";

const ctx = { token: "t", organizationId: "org-1" };

describe("clinic results API client", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("lists released reports with pagination", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: [
        {
          order_code: "ORD-1",
          result_code: "RES-1",
          patient_code: "P-1",
          patient_name: "Nguyen Van A",
          released_at: "2026-11-07T10:00:00",
        },
      ],
      pagination: { total: 7 },
    });
    const result = await listClinicReports(ctx, 2, 10);
    expect(result.items[0].order_code).toBe("ORD-1");
    expect(result.total).toBe(7);
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/clinic-results/reports?page=2&limit=10",
      expect.objectContaining({ token: "t", organizationId: "org-1" }),
    );
  });

  it("falls back to item count when pagination is missing", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: [] });
    const result = await listClinicReports(ctx);
    expect(result).toEqual({ items: [], total: 0 });
  });

  it("encodes the order code when opening a report", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: { order_code: "A/B", html_content: "<p>x</p>" },
    });
    const detail = await getClinicReport(ctx, "A/B");
    expect(detail.html_content).toBe("<p>x</p>");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/clinic-results/reports/A%2FB",
      expect.objectContaining({ token: "t" }),
    );
  });

  it("propagates errors so the page can show them", async () => {
    vi.mocked(apiRequest).mockRejectedValue(new Error("boom"));
    await expect(getClinicReport(ctx, "X")).rejects.toThrow("boom");
  });
});
