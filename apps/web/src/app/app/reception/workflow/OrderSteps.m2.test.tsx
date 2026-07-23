"use client";

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/reception", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/reception")>("@/lib/api/reception");
  return {
    ...actual,
    fetchReceptionOrder: vi.fn(),
    collectReceptionPayment: vi.fn(),
  };
});

import { collectReceptionPayment, fetchReceptionOrder } from "@/lib/api/reception";
import { ApiError } from "@/lib/errors";

import { PaymentStep } from "./OrderSteps";

const unpaidDetail = {
  order: {
    order_code: "ORD-1",
    patient_code: "P-1",
    status: "payment_pending",
    items: [{ test_code: "CBC", test_name: "CBC", unit_price: 100000 }],
  },
  pricing: { subtotal: 100000, discount: 0, total: 100000 },
  payment_summary: {
    order_total: 100000,
    paid_amount: 0,
    outstanding_amount: 100000,
    status: "unpaid",
    payment_methods_supported: ["cash", "transfer", "qr"],
    partial_payments_supported: false,
  },
  payment: null,
};

const paidDetail = {
  ...unpaidDetail,
  order: { ...unpaidDetail.order, status: "paid" },
  payment_summary: {
    order_total: 100000,
    paid_amount: 100000,
    outstanding_amount: 0,
    status: "paid",
    payment_methods_supported: ["cash", "transfer", "qr"],
    partial_payments_supported: false,
  },
  payment: {
    receipt_number: "RCT-1",
    payment_method: "cash",
    amount: 100000,
    paid_at: "2026-07-24T01:00:00Z",
    created_by: "cashier@dxcon.test",
  },
};

function renderPayment() {
  return render(
    <PaymentStep
      accessToken="t"
      organizationId="org"
      patient={{ patientCode: "P-1", patientName: "Ada" }}
      orderRef="ORD-1"
      pricing={{ subtotal: 100000, discount: 0, total: 100000 }}
      order={{ order_code: "ORD-1" }}
      onReset={vi.fn()}
      cashierLabel="cashier@dxcon.test"
    />,
  );
}

describe("Reception Milestone 2 PaymentStep", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(fetchReceptionOrder).mockReset();
    vi.mocked(collectReceptionPayment).mockReset();
    vi.mocked(fetchReceptionOrder).mockResolvedValue(unpaidDetail);
  });

  it("rejects overpayment client-side", async () => {
    const user = userEvent.setup();
    renderPayment();
    expect(await screen.findByRole("button", { name: "Collect payment" })).toBeInTheDocument();
    const amount = screen.getByLabelText("Amount due");
    await user.clear(amount);
    await user.type(amount, "150000");
    await user.click(screen.getByRole("button", { name: "Collect payment" }));
    expect(await screen.findByText(/Overpayment not allowed/i)).toBeInTheDocument();
    expect(collectReceptionPayment).not.toHaveBeenCalled();
  });

  it("rejects partial payment client-side", async () => {
    const user = userEvent.setup();
    renderPayment();
    await screen.findByRole("button", { name: "Collect payment" });
    const amount = screen.getByLabelText("Amount due");
    await user.clear(amount);
    await user.type(amount, "50000");
    await user.click(screen.getByRole("button", { name: "Collect payment" }));
    expect(await screen.findByText(/Partial payments are not supported/i)).toBeInTheDocument();
    expect(collectReceptionPayment).not.toHaveBeenCalled();
  });

  it("collects full payment and shows receipt", async () => {
    const user = userEvent.setup();
    vi.mocked(collectReceptionPayment).mockResolvedValue({
      payment: paidDetail.payment,
      invoice: { invoice_no: "INV-1", status: "paid" },
      order_status: "paid",
      payment_summary: paidDetail.payment_summary,
      idempotent_replay: false,
    });
    vi.mocked(fetchReceptionOrder)
      .mockResolvedValueOnce(unpaidDetail)
      .mockResolvedValue(paidDetail);

    renderPayment();
    await screen.findByRole("button", { name: "Collect payment" });
    await user.click(screen.getByRole("button", { name: "Collect payment" }));

    await waitFor(() =>
      expect(collectReceptionPayment).toHaveBeenCalledWith(
        expect.objectContaining({ token: "t" }),
        "ORD-1",
        expect.objectContaining({
          payment_method: "cash",
          amount: 100000,
          idempotency_key: expect.stringMatching(/^pay-/),
        }),
      ),
    );
    expect(await screen.findByText("Receipt")).toBeInTheDocument();
    expect(screen.getByText("RCT-1")).toBeInTheDocument();
    expect(screen.getByText("cashier@dxcon.test")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Print receipt" })).toBeInTheDocument();
  });

  it("locks duplicate submit while payment is in flight", async () => {
    const user = userEvent.setup();
    let resolvePay!: (value: unknown) => void;
    const payPromise = new Promise((resolve) => {
      resolvePay = resolve;
    });
    vi.mocked(collectReceptionPayment).mockImplementation(() => payPromise as never);

    renderPayment();
    const button = await screen.findByRole("button", { name: "Collect payment" });
    await user.click(button);
    await waitFor(() => expect(collectReceptionPayment).toHaveBeenCalledTimes(1));
    await user.click(screen.getByRole("button", { name: /Recording payment/i }));
    expect(collectReceptionPayment).toHaveBeenCalledTimes(1);

    resolvePay({
      payment: paidDetail.payment,
      invoice: null,
      order_status: "paid",
      payment_summary: paidDetail.payment_summary,
      idempotent_replay: false,
    });
    vi.mocked(fetchReceptionOrder).mockResolvedValue(paidDetail);
    await screen.findByText("Receipt");
  });

  it("surfaces backend payment errors", async () => {
    const user = userEvent.setup();
    vi.mocked(collectReceptionPayment).mockRejectedValue(
      new ApiError("Overpayment is not allowed", 400, { error: "Overpayment is not allowed" }),
    );
    renderPayment();
    await screen.findByRole("button", { name: "Collect payment" });
    await user.click(screen.getByRole("button", { name: "Collect payment" }));
    expect(await screen.findByText(/Overpayment is not allowed/i)).toBeInTheDocument();
  });
});
