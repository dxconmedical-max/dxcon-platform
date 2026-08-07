"use client";

import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/reception", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/reception")>("@/lib/api/reception");
  return {
    ...actual,
    searchReceptionPatients: vi.fn(),
    registerWalkIn: vi.fn(),
    fetchReceptionPatient: vi.fn(),
    fetchReceptionTests: vi.fn(),
    createReceptionOrder: vi.fn(),
    fetchReceptionOrder: vi.fn(),
  };
});

import {
  createReceptionOrder,
  fetchReceptionOrder,
  fetchReceptionPatient,
  fetchReceptionTests,
  registerWalkIn,
  searchReceptionPatients,
} from "@/lib/api/reception";
import { ApiError } from "@/lib/errors";

import {
  CatalogSelectStep,
  OrderConfirmationStep,
  PatientStep,
  ReviewPricingStep,
  type CatalogSelection,
  type CollectionRequestDraft,
} from "./Milestone1Steps";

const deskCollection: CollectionRequestDraft = {
  mode: "AT_RECEPTION",
  specimen_type: "BLOOD",
};

const patient = { patientCode: "P-1", patientName: "Ada" };

const catalogItem = {
  id: "t1",
  code: "CBC",
  name: "Complete Blood Count",
  price: 100_000,
  category: "Hematology",
  sample_type: "Blood",
  turnaround_hours: 24,
};

function selection(overrides: Partial<CatalogSelection> = {}): CatalogSelection {
  return {
    testIds: ["t1"],
    tests: [catalogItem],
    discount: 0,
    note: "",
    estimateSubtotal: 100_000,
    estimateTotal: 100_000,
    ...overrides,
  };
}

describe("Reception Milestone 1 steps", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(searchReceptionPatients).mockReset();
    vi.mocked(registerWalkIn).mockReset();
    vi.mocked(fetchReceptionPatient).mockReset();
    vi.mocked(fetchReceptionTests).mockReset();
    vi.mocked(createReceptionOrder).mockReset();
    vi.mocked(fetchReceptionOrder).mockReset();
  });

  it("ignores stale patient search responses", async () => {
    const user = userEvent.setup();
    let resolveFirst: ((value: { items: never[]; total: number }) => void) | undefined;
    const first = new Promise<{ items: never[]; total: number }>((resolve) => {
      resolveFirst = resolve;
    });
    vi.mocked(searchReceptionPatients)
      .mockImplementationOnce(() => first)
      .mockResolvedValueOnce({
        items: [{ patient_code: "P-2", full_name: "Bea", phone: "0911" }],
        total: 1,
      });

    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.type(screen.getByRole("textbox", { name: "Patient search" }), "aa");
    await waitFor(() => expect(searchReceptionPatients).toHaveBeenCalled());
    await user.type(screen.getByRole("textbox", { name: "Patient search" }), "bb");
    await waitFor(() => expect(searchReceptionPatients).toHaveBeenCalledTimes(2));
    resolveFirst?.({ items: [], total: 0 });
    expect(await screen.findByText("Bea")).toBeInTheDocument();
    expect(screen.queryByText(/no patients found/i)).not.toBeInTheDocument();
  });

  it("surfaces backend validation on patient create", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(registerWalkIn).mockRejectedValue(
      new ApiError("Phone format invalid", 400, { error: "Phone format invalid" }),
    );
    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.type(screen.getByLabelText("Full name *"), "Bad Phone");
    await user.type(screen.getByLabelText("Phone *"), "bad");
    await user.click(screen.getByRole("button", { name: "Register & continue" }));
    expect(await screen.findByText("Phone format invalid")).toBeInTheDocument();
  });

  it("prevents double-submit on patient create", async () => {
    const user = userEvent.setup();
    let resolveRegister: ((value: unknown) => void) | undefined;
    vi.mocked(searchReceptionPatients).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(registerWalkIn).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRegister = resolve as (value: unknown) => void;
        }) as ReturnType<typeof registerWalkIn>,
    );
    vi.mocked(fetchReceptionPatient).mockResolvedValue({
      patient_code: "P-SLOW",
      full_name: "Slow",
      phone: "0900111222",
    });
    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.type(screen.getByLabelText("Full name *"), "Slow");
    await user.type(screen.getByLabelText("Phone *"), "0900111222");
    const submit = screen.getByRole("button", { name: "Register & continue" });
    await user.click(submit);
    await user.click(submit);
    expect(registerWalkIn).toHaveBeenCalledTimes(1);
    resolveRegister?.({
      patient_code: "P-SLOW",
      message: "ok",
      patient: { patient_code: "P-SLOW", full_name: "Slow", phone: "0900111222" },
      warnings: [],
    });
  });

  it("blocks empty test list on order create", async () => {
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={selection({ testIds: [], tests: [] })}
        onBack={vi.fn()}
        onCreated={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Create laboratory order" }));
    expect(await screen.findByText(/select at least one test/i)).toBeInTheDocument();
    expect(createReceptionOrder).not.toHaveBeenCalled();
  });

  it("shows permission denial on patient search", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockRejectedValue(
      new ApiError("Forbidden", 403, { error: "Forbidden" }),
    );
    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.type(screen.getByRole("textbox", { name: "Patient search" }), "x");
    expect(await screen.findByText("Forbidden")).toBeInTheDocument();
  });

  it("searches catalog and shows specimen, TAT, and price", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({ items: [catalogItem], total: 1 });
    render(
      <CatalogSelectStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        onBack={vi.fn()}
        onContinue={vi.fn()}
      />,
    );
    await screen.findByText("CBC");
    expect(screen.getByText("Blood")).toBeInTheDocument();
    expect(screen.getByText("24")).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Catalog search" }), "CBC");
    await waitFor(() =>
      expect(fetchReceptionTests).toHaveBeenCalledWith(
        expect.objectContaining({ token: "t" }),
        expect.objectContaining({ q: "CBC" }),
      ),
    );
  });

  it("shows catalog empty and failure states", async () => {
    vi.mocked(fetchReceptionTests).mockResolvedValueOnce({ items: [], total: 0 });
    const { rerender } = render(
      <CatalogSelectStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        onBack={vi.fn()}
        onContinue={vi.fn()}
      />,
    );
    expect(await screen.findByText(/no tests found/i)).toBeInTheDocument();

    vi.mocked(fetchReceptionTests).mockRejectedValueOnce(
      new ApiError("Catalog unavailable", 500, { error: "Catalog unavailable" }),
    );
    rerender(
      <CatalogSelectStep
        accessToken="t2"
        organizationId="org"
        patient={patient}
        onBack={vi.fn()}
        onContinue={vi.fn()}
      />,
    );
    expect(await screen.findByText("Catalog unavailable")).toBeInTheDocument();
  });

  it("adds and removes tests without duplicates", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({ items: [catalogItem], total: 1 });
    const onContinue = vi.fn();
    render(
      <CatalogSelectStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        onBack={vi.fn()}
        onContinue={onContinue}
      />,
    );
    await screen.findByText("CBC");
    const checkbox = within(screen.getByRole("table")).getByRole("checkbox");
    await user.click(checkbox);
    expect(screen.getByText(/Selected 1/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Remove CBC" }));
    expect(screen.getByText(/Selected 0/i)).toBeInTheDocument();
    await user.click(checkbox);
    await user.click(checkbox);
    expect(screen.getByText(/Selected 0/i)).toBeInTheDocument();
    await user.click(checkbox);
    await user.click(screen.getByRole("button", { name: "Continue to collection request" }));
    expect(onContinue).toHaveBeenCalledWith(
      expect.objectContaining({
        testIds: ["t1"],
        estimateTotal: 100_000,
      }),
    );
  });

  it("blocks create when patient or tests missing", async () => {
    const onCreated = vi.fn();
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "", patientName: "Ghost" }}
        collectionRequest={deskCollection}
        selection={selection({ testIds: [], tests: [] })}
        onBack={vi.fn()}
        onCreated={onCreated}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Create laboratory order" }));
    expect(await screen.findByText(/select a patient/i)).toBeInTheDocument();
    expect(createReceptionOrder).not.toHaveBeenCalled();
    expect(onCreated).not.toHaveBeenCalled();
  });

  it("creates order with authoritative pricing", async () => {
    const user = userEvent.setup();
    vi.mocked(createReceptionOrder).mockResolvedValue({
      order: { order_code: "ORD-1", status: "payment_pending" },
      invoice: {},
      pricing: { subtotal: 100_000, discount: 0, total: 100_000, tax: null },
    });
    const onCreated = vi.fn();
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={selection()}
        onBack={vi.fn()}
        onCreated={onCreated}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Create laboratory order" }));
    await waitFor(() =>
      expect(onCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          orderRef: "ORD-1",
          pricing: expect.objectContaining({ total: 100_000 }),
        }),
      ),
    );
  });

  it("requires confirmation when backend price differs from estimate", async () => {
    const user = userEvent.setup();
    vi.mocked(createReceptionOrder).mockResolvedValue({
      order: { order_code: "ORD-DRIFT", status: "payment_pending" },
      invoice: {},
      pricing: { subtotal: 120_000, discount: 0, total: 120_000 },
    });
    const onCreated = vi.fn();
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={selection()}
        onBack={vi.fn()}
        onCreated={onCreated}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Create laboratory order" }));
    expect(await screen.findByText(/differs from estimate/i)).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Confirm backend total" }));
    expect(onCreated).toHaveBeenCalledWith(
      expect.objectContaining({
        orderRef: "ORD-DRIFT",
        pricing: expect.objectContaining({ total: 120_000 }),
      }),
    );
  });

  it("handles pricing/order create failure without advancing", async () => {
    const user = userEvent.setup();
    vi.mocked(createReceptionOrder).mockRejectedValue(
      new ApiError("Price list unavailable", 409, { error: "Price list unavailable" }),
    );
    const onCreated = vi.fn();
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={selection()}
        onBack={vi.fn()}
        onCreated={onCreated}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Create laboratory order" }));
    expect(await screen.findByText("Price list unavailable")).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
  });

  it("prevents duplicate order submit while in flight", async () => {
    const user = userEvent.setup();
    let resolveCreate: ((value: unknown) => void) | undefined;
    vi.mocked(createReceptionOrder).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveCreate = resolve as (value: unknown) => void;
        }) as ReturnType<typeof createReceptionOrder>,
    );
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={selection()}
        onBack={vi.fn()}
        onCreated={vi.fn()}
      />,
    );
    const btn = screen.getByRole("button", { name: "Create laboratory order" });
    await user.click(btn);
    await user.click(btn);
    expect(createReceptionOrder).toHaveBeenCalledTimes(1);
    resolveCreate?.({
      order: { order_code: "ORD-1" },
      invoice: {},
      pricing: { subtotal: 100_000, discount: 0, total: 100_000 },
    });
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Creating order…" })).not.toBeInTheDocument(),
    );
  });

  it("shows permission denial on order create", async () => {
    const user = userEvent.setup();
    vi.mocked(createReceptionOrder).mockRejectedValue(
      new ApiError("Forbidden", 403, { error: "Forbidden" }),
    );
    render(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={selection()}
        onBack={vi.fn()}
        onCreated={vi.fn()}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Create laboratory order" }));
    expect(await screen.findByText("Forbidden")).toBeInTheDocument();
  });

  it("confirms order and refreshes persistence via read endpoint", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionOrder).mockResolvedValue({
      order: {
        order_code: "ORD-1",
        patient_code: "P-1",
        status: "payment_pending",
        items: [{ test_code: "CBC" }],
      },
      pricing: { subtotal: 100_000, discount: 0, total: 100_000 },
      payment_summary: {
        order_total: 100_000,
        paid_amount: 0,
        outstanding_amount: 100_000,
        status: "unpaid",
      },
    });
    render(
      <OrderConfirmationStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        orderRef="ORD-1"
        pricing={{ subtotal: 90_000, discount: 0, total: 90_000 }}
        order={{ order_code: "ORD-1", status: "payment_pending" }}
        onCreateAnother={vi.fn()}
      />,
    );
    expect(await screen.findByText("ORD-1")).toBeInTheDocument();
    await waitFor(() => expect(fetchReceptionOrder).toHaveBeenCalled());
    expect(screen.getByText(/Authoritative total/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(fetchReceptionOrder).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("link", { name: "Open order" })).toHaveAttribute(
      "href",
      "/app/reception/workflow?order=ORD-1",
    );
  });

  it("happy path: catalog selection then successful create", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({ items: [catalogItem], total: 1 });
    vi.mocked(createReceptionOrder).mockResolvedValue({
      order: { order_code: "ORD-HAPPY", status: "payment_pending" },
      invoice: {},
      pricing: { subtotal: 100_000, discount: 0, total: 100_000 },
    });
    const onCreated = vi.fn();
    let captured: CatalogSelection | null = null;
    const { rerender } = render(
      <CatalogSelectStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        onBack={vi.fn()}
        onContinue={(next) => {
          captured = next;
        }}
      />,
    );
    await screen.findByText("CBC");
    await user.click(within(screen.getByRole("table")).getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Continue to collection request" }));
    expect(captured).not.toBeNull();
    rerender(
      <ReviewPricingStep
        accessToken="t"
        organizationId="org"
        patient={patient}
        collectionRequest={deskCollection}
        selection={captured!}
        onBack={vi.fn()}
        onCreated={onCreated}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Create laboratory order" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    expect(vi.mocked(createReceptionOrder).mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({
        patient_code: "P-1",
        test_catalog_ids: ["t1"],
        collection_mode: "AT_RECEPTION",
        specimen_type: "BLOOD",
      }),
    );
  });
});
