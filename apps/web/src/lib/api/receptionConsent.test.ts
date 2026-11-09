import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import { getPatientConsents, recordPatientConsents } from "./receptionConsent";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception consent API client", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("encodes the patient code when reading consents", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: { patient_code: "P/1", required: "LAB_TEST", consents: {} },
    });
    const result = await getPatientConsents(ctx, "P/1");
    expect(result.required).toBe("LAB_TEST");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/patients/P%2F1/consents",
      expect.objectContaining({ token: "t", organizationId: "org-1" }),
    );
  });

  it("posts the decisions with method and document reference", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: { patient_code: "P-1", required: "LAB_TEST", consents: {} },
    });
    await recordPatientConsents(ctx, "P-1", {
      consents: [{ consent_type: "LAB_TEST", granted: true }],
      method: "PAPER",
      document_ref: "FORM-1",
    });
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/patients/P-1/consents",
      expect.objectContaining({
        method: "POST",
        body: {
          consents: [{ consent_type: "LAB_TEST", granted: true }],
          method: "PAPER",
          document_ref: "FORM-1",
        },
      }),
    );
  });
});
