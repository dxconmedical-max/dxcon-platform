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

import { OrderCreatedStep, PatientStep, TestsStep } from "./OrderSteps";

describe("Reception Milestone 1 UI integration", () => {
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

  it("searches patients with debounce and selects one", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockResolvedValue({
      items: [{ patient_code: "P-1", full_name: "Ada", phone: "0900" }],
      total: 1,
    });
    const onSelect = vi.fn();
    render(<PatientStep accessToken="t" organizationId="org" onSelect={onSelect} />);
    await user.type(screen.getByRole("textbox", { name: "Patient search" }), "Ada");
    await waitFor(() => expect(searchReceptionPatients).toHaveBeenCalled(), { timeout: 2000 });
    await user.click(await screen.findByRole("button", { name: "Select" }));
    expect(onSelect).toHaveBeenCalledWith({ patientCode: "P-1", patientName: "Ada" });
  });

  it("shows empty search state", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockResolvedValue({ items: [], total: 0 });
    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.type(screen.getByRole("textbox", { name: "Patient search" }), "nobody");
    expect(await screen.findByText(/no patients found/i)).toBeInTheDocument();
  });

  it("shows search failure with retry", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockRejectedValue(
      new ApiError("Forbidden", 403, { error: "Forbidden" }),
    );
    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.type(screen.getByRole("textbox", { name: "Patient search" }), "x");
    expect(await screen.findByText("Forbidden")).toBeInTheDocument();
  });

  it("creates a patient and confirms persistence", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(registerWalkIn).mockResolvedValue({
      patient_code: "P-NEW",
      message: "ok",
      patient: { patient_code: "P-NEW", full_name: "New", phone: "0900" },
      warnings: [],
    });
    vi.mocked(fetchReceptionPatient).mockResolvedValue({
      patient_code: "P-NEW",
      full_name: "New",
      phone: "0900",
    });
    const onSelect = vi.fn();
    render(<PatientStep accessToken="t" organizationId="org" onSelect={onSelect} />);
    await user.type(screen.getByLabelText("Full name *"), "New");
    await user.type(screen.getByLabelText("Phone *"), "0900111222");
    await user.click(screen.getByRole("button", { name: "Register & continue" }));
    await waitFor(() =>
      expect(onSelect).toHaveBeenCalledWith({
        patientCode: "P-NEW",
        patientName: "New",
      }),
    );
    expect(fetchReceptionPatient).toHaveBeenCalled();
  });

  it("shows client validation failure when name/phone missing", async () => {
    const user = userEvent.setup();
    render(<PatientStep accessToken="t" organizationId="org" onSelect={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Register & continue" }));
    expect(await screen.findByText(/full name and phone are required/i)).toBeInTheDocument();
    expect(registerWalkIn).not.toHaveBeenCalled();
  });

  it("surfaces duplicate detection and allows using existing patient", async () => {
    const user = userEvent.setup();
    vi.mocked(searchReceptionPatients).mockResolvedValue({
      items: [{ patient_code: "P-DUP", full_name: "Dup", phone: "0900999888" }],
      total: 1,
    });
    const onSelect = vi.fn();
    render(<PatientStep accessToken="t" organizationId="org" onSelect={onSelect} />);
    await user.type(screen.getByLabelText("Full name *"), "Dup");
    await user.type(screen.getByLabelText("Phone *"), "0900999888");
    await user.click(screen.getByRole("button", { name: "Register & continue" }));
    expect(await screen.findByText(/possible duplicate patient/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Use existing" }));
    expect(onSelect).toHaveBeenCalledWith({ patientCode: "P-DUP", patientName: "Dup" });
    expect(registerWalkIn).not.toHaveBeenCalled();
  });

  it("selects a package category and creates an order once", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({
      items: [
        {
          id: "t1",
          code: "CBC",
          name: "CBC",
          price: 100,
          category: "Hematology",
          sample_type: "Blood",
          turnaround_hours: 24,
        },
        {
          id: "t2",
          code: "DIFF",
          name: "Diff",
          price: 50,
          category: "Hematology",
          sample_type: "Blood",
        },
      ],
      total: 2,
    });
    vi.mocked(createReceptionOrder).mockResolvedValue({
      order: { order_code: "ORD-PKG", items: [{ test_code: "CBC" }, { test_code: "DIFF" }] },
      invoice: {},
      pricing: { subtotal: 150, discount: 0, total: 150 },
    });
    const onOrderCreated = vi.fn();
    render(
      <TestsStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "P-1", patientName: "Ada" }}
        onOrderCreated={onOrderCreated}
      />,
    );
    await screen.findByText("Packages (by category)");
    const packageCheckbox = screen.getAllByRole("checkbox")[0];
    await user.click(packageCheckbox);
    await user.click(screen.getByRole("button", { name: "Create order" }));
    await waitFor(() => expect(createReceptionOrder).toHaveBeenCalledTimes(1));
    const payload = vi.mocked(createReceptionOrder).mock.calls[0]?.[1];
    expect(payload?.test_catalog_ids).toEqual(expect.arrayContaining(["t1", "t2"]));
    expect(payload?.test_catalog_ids).toHaveLength(2);
    expect(onOrderCreated).toHaveBeenCalledWith(
      "ORD-PKG",
      { subtotal: 150, discount: 0, total: 150 },
      expect.objectContaining({ order_code: "ORD-PKG" }),
    );
  });

  it("adds and removes a test before create", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({
      items: [
        {
          id: "t1",
          code: "CBC",
          name: "CBC",
          price: 100,
          category: "Hematology",
          sample_type: "Blood",
        },
      ],
      total: 1,
    });
    render(
      <TestsStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "P-1", patientName: "Ada" }}
        onOrderCreated={vi.fn()}
      />,
    );
    await screen.findAllByText("CBC");
    const table = screen.getByRole("table");
    const testCheckbox = within(table).getByRole("checkbox");
    await user.click(testCheckbox);
    expect(screen.getByText(/1 tests/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /CBC ×/i }));
    expect(screen.getByText(/0 tests/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create order" })).toBeDisabled();
  });

  it("prevents duplicate order submit while in flight", async () => {
    const user = userEvent.setup();
    let resolveCreate: ((value: unknown) => void) | undefined;
    vi.mocked(fetchReceptionTests).mockResolvedValue({
      items: [{ id: "t1", code: "CBC", name: "CBC", price: 100, category: "Hematology" }],
      total: 1,
    });
    vi.mocked(createReceptionOrder).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveCreate = resolve as (value: unknown) => void;
        }) as ReturnType<typeof createReceptionOrder>,
    );
    render(
      <TestsStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "P-1", patientName: "Ada" }}
        onOrderCreated={vi.fn()}
      />,
    );
    await screen.findAllByText("CBC");
    await user.click(within(screen.getByRole("table")).getByRole("checkbox"));
    const createBtn = screen.getByRole("button", { name: "Create order" });
    await user.click(createBtn);
    await user.click(createBtn);
    expect(createReceptionOrder).toHaveBeenCalledTimes(1);
    resolveCreate?.({
      order: { order_code: "ORD-1" },
      invoice: {},
      pricing: { subtotal: 100, discount: 0, total: 100 },
    });
    await waitFor(() => expect(screen.getByRole("button", { name: "Create order" })).toBeEnabled());
  });

  it("shows partial failure from order create without advancing", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({
      items: [{ id: "t1", code: "CBC", name: "CBC", price: 100, category: "Hematology" }],
      total: 1,
    });
    vi.mocked(createReceptionOrder).mockRejectedValue(
      new ApiError("Patient not found", 400, { error: "Patient not found" }),
    );
    const onOrderCreated = vi.fn();
    render(
      <TestsStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "missing", patientName: "Ghost" }}
        onOrderCreated={onOrderCreated}
      />,
    );
    await screen.findAllByText("CBC");
    await user.click(within(screen.getByRole("table")).getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Create order" }));
    expect(await screen.findByText("Patient not found")).toBeInTheDocument();
    expect(onOrderCreated).not.toHaveBeenCalled();
  });

  it("prevents duplicate catalog items when toggling the same test", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchReceptionTests).mockResolvedValue({
      items: [
        {
          id: "t1",
          code: "CBC",
          name: "CBC",
          price: 100,
          category: "Hematology",
          sample_type: "Blood",
        },
      ],
      total: 1,
    });
    vi.mocked(createReceptionOrder).mockResolvedValue({
      order: { order_code: "ORD-1", items: [{ test_code: "CBC" }] },
      invoice: {},
      pricing: { subtotal: 100, discount: 0, total: 100 },
    });
    const onOrderCreated = vi.fn();
    render(
      <TestsStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "P-1", patientName: "Ada" }}
        onOrderCreated={onOrderCreated}
      />,
    );
    await screen.findAllByText("CBC");
    const table = screen.getByRole("table");
    const testCheckbox = within(table).getByRole("checkbox");
    await user.click(testCheckbox);
    await user.click(screen.getByRole("button", { name: "Create order" }));
    await waitFor(() => expect(createReceptionOrder).toHaveBeenCalled());
    const payload = vi.mocked(createReceptionOrder).mock.calls[0]?.[1];
    expect(payload?.test_catalog_ids).toEqual(["t1"]);
    expect(onOrderCreated).toHaveBeenCalledWith(
      "ORD-1",
      { subtotal: 100, discount: 0, total: 100 },
      expect.objectContaining({ order_code: "ORD-1" }),
    );
  });

  it("refreshes authoritative order totals", async () => {
    vi.mocked(fetchReceptionOrder).mockResolvedValue({
      order: {
        order_code: "ORD-1",
        patient_code: "P-1",
        status: "payment_pending",
        items: [{ test_code: "CBC", test_name: "CBC", unit_price: 100 }],
      },
      pricing: { subtotal: 100, discount: 0, total: 100 },
    });
    vi.mocked(fetchReceptionPatient).mockResolvedValue({
      patient_code: "P-1",
      full_name: "Ada",
    });
    render(
      <OrderCreatedStep
        accessToken="t"
        organizationId="org"
        patient={{ patientCode: "P-1", patientName: "Ada" }}
        orderRef="ORD-1"
        pricing={{ subtotal: 90, discount: 0, total: 90 }}
        order={{ order_code: "ORD-1" }}
        onReset={vi.fn()}
      />,
    );
    expect(await screen.findByText("Authoritative total (API)")).toBeInTheDocument();
    await waitFor(() =>
      expect(fetchReceptionOrder).toHaveBeenCalledWith(
        expect.objectContaining({ token: "t" }),
        "ORD-1",
      ),
    );
  });
});
