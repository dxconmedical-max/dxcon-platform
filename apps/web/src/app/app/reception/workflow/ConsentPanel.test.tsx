import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/receptionConsent", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/receptionConsent")>(
    "@/lib/api/receptionConsent",
  );
  return { ...actual, getPatientConsents: vi.fn(), recordPatientConsents: vi.fn() };
});

import { getPatientConsents, recordPatientConsents } from "@/lib/api/receptionConsent";

import { ConsentPanel } from "./ConsentPanel";

const none = {
  patient_code: "P-1",
  required: "LAB_TEST" as const,
  consents: {
    LAB_TEST: null,
    PARTNER_LAB: null,
    CLINIC_SHARE: null,
    CONTACT: null,
    OVERSEAS_STORAGE: null,
  },
};

describe("ConsentPanel", () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    vi.mocked(getPatientConsents).mockReset();
    vi.mocked(recordPatientConsents).mockReset();
  });

  it("starts with every box empty and shows consent not recorded", async () => {
    vi.mocked(getPatientConsents).mockResolvedValue(none);
    render(<ConsentPanel accessToken="t" patientCode="P-1" />);
    await waitFor(() => expect(screen.getByText("Testing consent not recorded")).toBeTruthy());
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes.slice(0, 5).every((box) => !box.checked)).toBe(true);
  });

  it("saves the ticked decisions with the chosen method", async () => {
    vi.mocked(getPatientConsents).mockResolvedValue(none);
    vi.mocked(recordPatientConsents).mockResolvedValue({
      ...none,
      consents: {
        ...none.consents,
        LAB_TEST: { granted: true, status: "GRANTED", version: "draft-2026-11", recorded_at: null },
      },
    });
    const user = userEvent.setup();
    render(<ConsentPanel accessToken="t" patientCode="P-1" />);
    await waitFor(() => expect(screen.getByText("Testing consent not recorded")).toBeTruthy());

    await user.click(screen.getByLabelText(/Testing \(required\)/));
    await user.click(screen.getByRole("button", { name: "Save consent" }));

    await waitFor(() => expect(recordPatientConsents).toHaveBeenCalledTimes(1));
    const body = vi.mocked(recordPatientConsents).mock.calls[0][2];
    expect(body.method).toBe("PAPER");
    expect(body.consents.find((c) => c.consent_type === "LAB_TEST")?.granted).toBe(true);
    expect(body.consents.find((c) => c.consent_type === "CLINIC_SHARE")?.granted).toBe(false);
    await waitFor(() => expect(screen.getByText("Testing consent recorded")).toBeTruthy());
  });
});
