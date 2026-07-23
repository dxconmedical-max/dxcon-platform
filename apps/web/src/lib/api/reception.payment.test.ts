import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import {
  collectReceptionPayment,
  fetchReceptionOrder,
  RECEPTION_PAYMENT_TIMEOUT_MS,
} from "./reception";

const ctx = { token: "t", organizationId: "org-1" };

describe("reception Milestone 2 payment API", () => {
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
  });

  it("unpaid summary", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order: { order_code: "ORD-1", status: "payment_pending" },
        pricing: { subtotal: 100, discount: 0, total: 100 },
        payment_summary: {
          order_total: 100,
          paid_amount: 0,
          outstanding_amount: 100,
          status: "unpaid",
          payment_methods_supported: ["cash", "qr"],
          partial_payments_supported: false,
        },
        payment: null,
        invoice: { invoice_no: "INV-1", status: "unpaid" },
      },
    });
    const result = await fetchReceptionOrder(ctx, "ORD-1");
    expect(result.payment_summary?.status).toBe("unpaid");
    expect(result.payment_summary?.outstanding_amount).toBe(100);
    expect(result.payment).toBeNull();
    expect(result.invoice?.invoice_no).toBe("INV-1");
  });

  it("full payment", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        payment: { receipt_number: "RCT-1", payment_method: "cash", amount: 100, paid_at: "2026-07-24T00:00:00" },
        invoice: { invoice_no: "INV-1", status: "paid" },
        order_status: "paid",
        payment_summary: {
          order_total: 100,
          paid_amount: 100,
          outstanding_amount: 0,
          status: "paid",
        },
        idempotent_replay: false,
      },
    });
    const result = await collectReceptionPayment(ctx, "ORD-1", {
      payment_method: "cash",
      amount: 100,
      idempotency_key: "idem-1",
    });
    expect(result.payment?.receipt_number).toBe("RCT-1");
    expect(result.payment_summary.status).toBe("paid");
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/reception/workspace/orders/ORD-1/payment",
      expect.objectContaining({
        timeoutMs: RECEPTION_PAYMENT_TIMEOUT_MS,
        headers: expect.objectContaining({ "Idempotency-Key": "idem-1" }),
      }),
    );
  });

  it("partial rejected", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Partial payments are not supported", 400, {
        error: "Partial payments are not supported",
      }),
    );
    await expect(
      collectReceptionPayment(ctx, "ORD-1", {
        payment_method: "cash",
        amount: 50,
        idempotency_key: "p",
      }),
    ).rejects.toMatchObject({ status: 400 });
  });

  it("overpayment rejected", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Overpayment is not allowed", 400, { error: "Overpayment is not allowed" }),
    );
    await expect(
      collectReceptionPayment(ctx, "ORD-1", {
        payment_method: "cash",
        amount: 999,
        idempotency_key: "o",
      }),
    ).rejects.toMatchObject({ status: 400 });
  });

  it("invalid method rejected", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Invalid payment method: bitcoin", 400, {
        error: "Invalid payment method: bitcoin",
      }),
    );
    await expect(
      collectReceptionPayment(ctx, "ORD-1", {
        payment_method: "bitcoin",
        amount: 100,
        idempotency_key: "bad",
      }),
    ).rejects.toMatchObject({ status: 400 });
  });

  it("idempotent replay", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        payment: { receipt_number: "idem-1", payment_method: "cash", amount: 100 },
        payment_summary: {
          order_total: 100,
          paid_amount: 100,
          outstanding_amount: 0,
          status: "paid",
        },
        idempotent_replay: true,
      },
    });
    const result = await collectReceptionPayment(ctx, "ORD-1", {
      payment_method: "cash",
      amount: 100,
      idempotency_key: "idem-1",
    });
    expect(result.idempotent_replay).toBe(true);
    expect(result.payment?.receipt_number).toBe("idem-1");
  });

  it("backend failure", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Server boom", 500, { error: "Server boom" }),
    );
    await expect(
      collectReceptionPayment(ctx, "ORD-1", {
        payment_method: "cash",
        amount: 100,
        idempotency_key: "x",
      }),
    ).rejects.toMatchObject({ status: 500 });
  });

  it("timeout", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Request timed out", 408, { code: "TIMEOUT" }),
    );
    await expect(
      collectReceptionPayment(
        { ...ctx, timeoutMs: RECEPTION_PAYMENT_TIMEOUT_MS },
        "ORD-1",
        { payment_method: "cash", amount: 100, idempotency_key: "t" },
      ),
    ).rejects.toMatchObject({ status: 408, body: expect.objectContaining({ code: "TIMEOUT" }) });
  });

  it("refresh paid", async () => {
    vi.mocked(apiRequest).mockResolvedValue({
      success: true,
      data: {
        order: { order_code: "ORD-1", status: "paid" },
        pricing: { subtotal: 100, discount: 0, total: 100 },
        payment_summary: {
          order_total: 100,
          paid_amount: 100,
          outstanding_amount: 0,
          status: "paid",
        },
        payment: {
          receipt_number: "RCT-PAID",
          payment_method: "qr",
          amount: 100,
          paid_at: "2026-07-24T01:00:00Z",
          created_by: "cashier@dxcon.test",
        },
      },
    });
    const result = await fetchReceptionOrder(ctx, "ORD-1");
    expect(result.payment_summary?.status).toBe("paid");
    expect(result.payment?.receipt_number).toBe("RCT-PAID");
    expect(result.payment?.created_by).toBe("cashier@dxcon.test");
  });

  it("permission denial", async () => {
    vi.mocked(apiRequest).mockRejectedValue(
      new ApiError("Forbidden", 403, { error: "Forbidden" }),
    );
    await expect(
      collectReceptionPayment(ctx, "ORD-1", {
        payment_method: "cash",
        amount: 100,
        idempotency_key: "forbid",
      }),
    ).rejects.toMatchObject({ status: 403 });
  });

  it("happy path unpaid then collect then refresh paid", async () => {
    vi.mocked(apiRequest)
      .mockResolvedValueOnce({
        success: true,
        data: {
          order: { order_code: "ORD-H", status: "payment_pending" },
          pricing: { subtotal: 150000, discount: 0, total: 150000 },
          payment_summary: {
            order_total: 150000,
            paid_amount: 0,
            outstanding_amount: 150000,
            status: "unpaid",
          },
          payment: null,
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          payment: { receipt_number: "RCT-H", payment_method: "transfer", amount: 150000 },
          payment_summary: {
            order_total: 150000,
            paid_amount: 150000,
            outstanding_amount: 0,
            status: "paid",
          },
          idempotent_replay: false,
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          order: { order_code: "ORD-H", status: "paid" },
          pricing: { subtotal: 150000, discount: 0, total: 150000 },
          payment_summary: {
            order_total: 150000,
            paid_amount: 150000,
            outstanding_amount: 0,
            status: "paid",
          },
          payment: { receipt_number: "RCT-H", payment_method: "transfer", amount: 150000 },
        },
      });

    const unpaid = await fetchReceptionOrder(ctx, "ORD-H");
    expect(unpaid.payment_summary?.status).toBe("unpaid");
    const paid = await collectReceptionPayment(ctx, "ORD-H", {
      payment_method: "transfer",
      amount: 150000,
      idempotency_key: "happy-1",
    });
    expect(paid.payment_summary.status).toBe("paid");
    const refreshed = await fetchReceptionOrder(ctx, "ORD-H");
    expect(refreshed.payment_summary?.status).toBe("paid");
    expect(refreshed.payment?.receipt_number).toBe("RCT-H");
  });
});
