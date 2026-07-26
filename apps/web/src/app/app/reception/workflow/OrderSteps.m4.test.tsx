import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

vi.mock("@/lib/api/reception", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/reception")>("@/lib/api/reception");
  return {
    ...actual,
    fetchReceptionBarcodes: vi.fn(),
    fetchReceptionRequestForm: vi.fn(),
    fetchReceptionLabHandoff: vi.fn(),
    handoffReceptionOrderToLab: vi.fn(),
  };
});

import {
  fetchReceptionBarcodes,
  fetchReceptionLabHandoff,
  fetchReceptionRequestForm,
  handoffReceptionOrderToLab,
  RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
} from "@/lib/api/reception";

import { DocumentsStep } from "./OrderSteps";

const barcodes = {
  order_barcode: "BC-ORD-1",
  patient_barcode: "BC-PAT-P1",
  patient_qr: "dxcon:patient:P1",
  sample_barcodes: [
    {
      test_code: "CBC",
      test_name: "Complete Blood Count",
      specimen_code: "SMP-CBC-ORD-1",
      barcode: "BC-SMP-CBC-ORD-1",
      sample_type: "Blood",
    },
  ],
  generated_at: "2026-07-24T00:00:00.000Z",
  reprint: false,
};

const handoffSuccess = {
  order_code: "ORD-1",
  order_status: "lab_received",
  collection: { status: "delivered", accession_number: "ACC-1" },
  queue_entry: null,
  queue_reference: "ACC-1",
  laboratory: { id: null, name: "Central Laboratory" },
  accepted_at: "2026-07-24T02:00:00.000Z",
  handed_off: true,
  idempotent_replay: false,
};

function renderDocs() {
  return render(
    <DocumentsStep
      accessToken="t"
      organizationId="org"
      patient={{ patientCode: "P1", patientName: "Ada" }}
      orderRef="ORD-1"
      pricing={{ subtotal: 100, discount: 0, total: 100 }}
      payment={{ receipt_number: "RCT-1", payment_method: "cash", amount: 100 }}
      onReset={vi.fn()}
    />,
  );
}

describe("Reception Milestone 4 laboratory handoff UI", () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    vi.mocked(fetchReceptionBarcodes).mockReset();
    vi.mocked(fetchReceptionRequestForm).mockReset();
    vi.mocked(fetchReceptionLabHandoff).mockReset();
    vi.mocked(handoffReceptionOrderToLab).mockReset();
    vi.mocked(fetchReceptionBarcodes).mockResolvedValue(barcodes);
    vi.mocked(fetchReceptionRequestForm).mockResolvedValue({
      html: "<html><body>Lab Request Form ORD-1</body></html>",
      order_code: "ORD-1",
    });
    vi.mocked(fetchReceptionLabHandoff).mockResolvedValue({
      order_code: "ORD-1",
      order_status: "paid",
      collection: null,
      queue_entry: null,
      queue_reference: null,
      laboratory: { id: null, name: "Central Laboratory" },
      accepted_at: null,
      handed_off: false,
      idempotent_replay: false,
    });
  });

  it("hands off successfully and refreshes persisted status", async () => {
    const user = userEvent.setup();
    vi.mocked(handoffReceptionOrderToLab).mockResolvedValue(handoffSuccess);
    vi.mocked(fetchReceptionLabHandoff)
      .mockResolvedValueOnce({
        order_code: "ORD-1",
        order_status: "paid",
        collection: null,
        queue_entry: null,
        queue_reference: null,
        laboratory: { id: null, name: "Central Laboratory" },
        accepted_at: null,
        handed_off: false,
      })
      .mockResolvedValueOnce(handoffSuccess);

    renderDocs();
    expect(await screen.findByRole("button", { name: "Hand off to Laboratory" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Hand off to Laboratory" }));

    await waitFor(() => expect(handoffReceptionOrderToLab).toHaveBeenCalledTimes(1));
    expect(handoffReceptionOrderToLab).toHaveBeenCalledWith(
      expect.objectContaining({ timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS }),
      "ORD-1",
    );
    expect(await screen.findByText("ACC-1")).toBeInTheDocument();
    expect(screen.getByText("Central Laboratory")).toBeInTheDocument();
    expect(screen.getByText(/lab_received/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hand off to Laboratory" })).not.toBeInTheDocument();
    expect(vi.mocked(fetchReceptionLabHandoff).mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("shows controlled failure and allows retry", async () => {
    const user = userEvent.setup();
    vi.mocked(handoffReceptionOrderToLab)
      .mockRejectedValueOnce(
        new ApiError("Order must be paid before laboratory handoff", 400, {
          error: "Order must be paid before laboratory handoff",
        }),
      )
      .mockResolvedValueOnce(handoffSuccess);
    vi.mocked(fetchReceptionLabHandoff)
      .mockResolvedValueOnce({
        order_code: "ORD-1",
        order_status: "paid",
        collection: null,
        queue_entry: null,
        queue_reference: null,
        laboratory: { id: null, name: "Central Laboratory" },
        accepted_at: null,
        handed_off: false,
      })
      .mockResolvedValue(handoffSuccess);

    renderDocs();
    await user.click(await screen.findByRole("button", { name: "Hand off to Laboratory" }));
    expect(
      await screen.findByText(/Order must be paid before laboratory handoff/i),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry handoff" }));
    expect(await screen.findByText("ACC-1")).toBeInTheDocument();
  });

  it("disables duplicate submit while in flight", async () => {
    const user = userEvent.setup();
    let resolveHandoff: (value: typeof handoffSuccess) => void = () => undefined;
    vi.mocked(handoffReceptionOrderToLab).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveHandoff = resolve;
        }),
    );

    renderDocs();
    const button = await screen.findByRole("button", { name: "Hand off to Laboratory" });
    await user.click(button);
    expect(await screen.findByRole("button", { name: "Handing off…" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Handing off…" }));
    expect(handoffReceptionOrderToLab).toHaveBeenCalledTimes(1);
    resolveHandoff(handoffSuccess);
    vi.mocked(fetchReceptionLabHandoff).mockResolvedValue(handoffSuccess);
    await waitFor(() => expect(screen.getByText("ACC-1")).toBeInTheDocument());
  });

  it("surfaces timeout errors", async () => {
    const user = userEvent.setup();
    vi.mocked(handoffReceptionOrderToLab).mockRejectedValue(
      new ApiError("Request timed out", 408, { error: "Request timed out", code: "TIMEOUT" }),
    );
    renderDocs();
    await user.click(await screen.findByRole("button", { name: "Hand off to Laboratory" }));
    expect(await screen.findByText(/timed out/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry handoff" })).toBeInTheDocument();
  });
});
