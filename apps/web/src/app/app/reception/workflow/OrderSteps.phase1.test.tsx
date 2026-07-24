import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/layout/RoleDashboardHome", () => ({
  RoleDashboardHome: ({
    title,
    subtitle,
  }: {
    title: string;
    subtitle: string;
  }) => (
    <div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  ),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    accessToken: "token",
    activeOrganizationId: "org-1",
    can: () => true,
    role: "RECEPTION",
    user: { email: "reception@dxcon.test" },
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/reception", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/reception")>("@/lib/api/reception");
  return {
    ...actual,
    searchReceptionPatients: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    fetchReceptionTests: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  };
});

import ReceptionPage from "../page";
import ReceptionSearchPage from "../search/page";
import ReceptionRegisterPage from "../register/page";
import ReceptionWorkflowPage from "./page";
import { JourneyStepper } from "../_components/ui";

describe("Reception Phase 1 regression", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders dashboard Phase 1 journey", () => {
    render(<ReceptionPage />);
    expect(screen.getByText("Phase 1 journey")).toBeInTheDocument();
    expect(screen.getByText("Find or register patient")).toBeInTheDocument();
    expect(screen.getByText("Print barcode & order form")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Start order workflow/i })).toHaveAttribute(
      "href",
      "/app/reception/workflow",
    );
  });

  it("renders patient search controls", () => {
    render(<ReceptionSearchPage />);
    expect(screen.getByLabelText("Patient search")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Search/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Register/i })).toBeInTheDocument();
  });

  it("renders registration required fields", () => {
    render(<ReceptionRegisterPage />);
    expect(screen.getByLabelText(/Full name/i)).toBeRequired();
    expect(screen.getByLabelText(/^Phone/i)).toBeRequired();
    expect(screen.getByRole("button", { name: /Register patient/i })).toBeInTheDocument();
  });

  it("renders order workflow Phase 1 stepper", () => {
    render(<ReceptionWorkflowPage />);
    expect(screen.getByText(/Reception Phase 1 — Order workflow/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Reception workflow steps")).toBeInTheDocument();
    expect(screen.getByText(/1\. Patient/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Tests & order number/)).toBeInTheDocument();
  });

  it("JourneyStepper marks active step", () => {
    render(<JourneyStepper steps={["A", "B", "C"] as const} activeIndex={1} />);
    expect(screen.getByText("2. B").closest("li")).toHaveAttribute("aria-current", "step");
  });
});
