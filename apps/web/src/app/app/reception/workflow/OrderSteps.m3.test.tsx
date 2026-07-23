import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/reception", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/reception")>("@/lib/api/reception");
  return {
    ...actual,
    fetchReceptionOrder: vi.fn(),
    collectReceptionPayment: vi.fn(),
    fetchReceptionBarcodes: vi.fn(),
    fetchReceptionRequestForm: vi.fn(),
  };
});

import {
  fetchReceptionBarcodes,
  fetchReceptionOrder,
  fetchReceptionRequestForm,
} from "@/lib/api/reception";

import { DocumentsStep } from "./OrderSteps";

describe("Reception Milestone 3 documents UI", () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    vi.mocked(fetchReceptionBarcodes).mockReset();
    vi.mocked(fetchReceptionRequestForm).mockReset();
    vi.mocked(fetchReceptionOrder).mockReset();
    vi.mocked(fetchReceptionBarcodes).mockResolvedValue({
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
          collection_requirement: "Follow standard collection SOP",
        },
      ],
      generated_at: "2026-07-24T00:00:00.000Z",
      reprint: false,
    });
    vi.mocked(fetchReceptionRequestForm).mockResolvedValue({
      html: "<html><body>Lab Request Form ORD-1</body></html>",
      order_code: "ORD-1",
      reprint: false,
    });
  });

  it("loads barcodes and requisition for paid order", async () => {
    render(
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
    expect(await screen.findByText("BC-ORD-1")).toBeInTheDocument();
    expect(screen.getByText("dxcon:patient:P1")).toBeInTheDocument();
    expect(screen.getByText("QR format valid")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Print labels" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open requisition" })).toBeInTheDocument();
  });

  it("shows backend eligibility error", async () => {
    vi.mocked(fetchReceptionBarcodes).mockRejectedValue(
      Object.assign(new Error("Order must be paid before barcode, QR, or requisition generation"), {
        name: "ApiError",
        status: 400,
        body: { error: "Order must be paid before barcode, QR, or requisition generation" },
      }),
    );
    // Use ApiError properly
    const { ApiError } = await import("@/lib/errors");
    vi.mocked(fetchReceptionBarcodes).mockRejectedValue(
      new ApiError("Order must be paid before barcode, QR, or requisition generation", 400, {
        error: "Order must be paid before barcode, QR, or requisition generation",
      }),
    );
    vi.mocked(fetchReceptionRequestForm).mockRejectedValue(
      new ApiError("Order must be paid before barcode, QR, or requisition generation", 400, {
        error: "Order must be paid before barcode, QR, or requisition generation",
      }),
    );
    render(
      <DocumentsStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "P1", patientName: "Ada" }}
        orderRef="ORD-1"
        pricing={{ subtotal: 100, discount: 0, total: 100 }}
        payment={null}
        onReset={vi.fn()}
      />,
    );
    expect(
      await screen.findByText(/Order must be paid before barcode/i),
    ).toBeInTheDocument();
  });

  it("reprint refresh calls APIs again", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionBarcodes)
      .mockResolvedValueOnce({
        order_barcode: "BC-ORD-1",
        patient_barcode: "BC-PAT-P1",
        patient_qr: "dxcon:patient:P1",
        sample_barcodes: [],
        reprint: false,
      })
      .mockResolvedValueOnce({
        order_barcode: "BC-ORD-1",
        patient_barcode: "BC-PAT-P1",
        patient_qr: "dxcon:patient:P1",
        sample_barcodes: [],
        reprint: true,
      });
    render(
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
    await screen.findByText("BC-ORD-1");
    await user.click(screen.getByRole("button", { name: "Reprint" }));
    await waitFor(() => expect(fetchReceptionBarcodes).toHaveBeenCalledTimes(2));
  });
});
