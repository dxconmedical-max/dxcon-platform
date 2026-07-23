import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();

type Gate = {
  isHydrated: boolean;
  bootstrapPhase: "idle" | "restoring" | "complete" | "failed";
  isInitializingSession: boolean;
  isAuthenticated: boolean;
  status: "authenticated" | "unauthenticated";
  error: string | null;
};

let authState: Gate = {
  isHydrated: true,
  bootstrapPhase: "complete",
  isInitializingSession: false,
  isAuthenticated: true,
  status: "authenticated",
  error: null,
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  usePathname: () => "/app/admin",
}));

vi.mock("@/hooks/useAuth", () => ({
  useRequireAuth: () => ({
    ...authState,
    isSubmittingLogin: false,
    isRefreshingSession: false,
    restoreSession: vi.fn(),
    logout: vi.fn(),
    clearTransientFlags: vi.fn(),
    clearError: vi.fn(),
    login: vi.fn(),
    selectOrganization: vi.fn(),
    resolveAfterLogin: vi.fn(),
    setHydrated: vi.fn(),
    user: { id: "1", email: "a@b.com", role: "ADMIN" },
    role: "ADMIN",
    accessToken: "tok",
    refreshToken: "ref",
    workspacePath: "/app/admin",
    capabilities: { workspace: "/app/admin", permissions: [], features: [] },
    can: () => true,
    canAny: () => true,
    canAll: () => true,
    hasFeature: () => true,
    isWorkspace: () => true,
    isOrganizationType: () => true,
  }),
}));

vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector?: (s: Record<string, unknown>) => unknown) => {
    const state = {
      restoreSession: vi.fn(),
      logout: vi.fn(),
      clearTransientFlags: vi.fn(),
      setState: vi.fn(),
    };
    return selector ? selector(state) : state;
  },
}));

vi.mock("@/components/layout/Header", () => ({
  Header: ({ title }: { title: string }) => <div>{title}</div>,
  MobileNav: () => null,
}));

vi.mock("@/components/layout/Sidebar", () => ({
  Sidebar: () => <nav>Sidebar</nav>,
}));

import { AppShell } from "./AppShell";

describe("AppShell after single-owner bootstrap", () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    replace.mockReset();
    authState = {
      isHydrated: true,
      bootstrapPhase: "complete",
      isInitializingSession: false,
      isAuthenticated: true,
      status: "authenticated",
      error: null,
    };
  });

  it("renders /app/admin shell after valid restored session", () => {
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>Admin workspace</div>
      </AppShell>,
    );
    expect(screen.getByText("Administration")).toBeInTheDocument();
    expect(screen.getByText("Admin workspace")).toBeInTheDocument();
  });

  it("shows spinner while bootstrapPhase is restoring", () => {
    authState = {
      ...authState,
      bootstrapPhase: "restoring",
      isAuthenticated: false,
      status: "unauthenticated",
    };
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>x</div>
      </AppShell>,
    );
    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();
  });

  it("restore failure exits spinner with controlled error", () => {
    authState = {
      isHydrated: true,
      bootstrapPhase: "failed",
      isInitializingSession: false,
      isAuthenticated: false,
      status: "unauthenticated",
      error: "Session restore timed out",
    };
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>x</div>
      </AppShell>,
    );
    expect(
      screen.getByRole("heading", { name: /Unable to load workspace/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(/timed out/i);
  });
});
