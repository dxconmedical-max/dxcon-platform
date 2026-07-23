import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
const restoreSession = vi.fn();
const logout = vi.fn();
const clearTransientFlags = vi.fn();

type AuthGate = {
  isHydrated: boolean;
  isInitializingSession: boolean;
  isAuthenticated: boolean;
  status: "authenticated" | "unauthenticated";
  error: string | null;
};

let authState: AuthGate = {
  isHydrated: true,
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
    restoreSession,
    logout,
    clearTransientFlags,
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
      restoreSession,
      logout,
      clearTransientFlags,
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

describe("AppShell bootstrap gates", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    replace.mockReset();
    restoreSession.mockReset();
    logout.mockReset();
    clearTransientFlags.mockReset();
    authState = {
      isHydrated: true,
      isInitializingSession: false,
      isAuthenticated: true,
      status: "authenticated",
      error: null,
    };
  });

  it("renders admin shell when authenticated (no infinite spinner)", () => {
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>Admin workspace</div>
      </AppShell>,
    );
    expect(screen.getByText("Administration")).toBeInTheDocument();
    expect(screen.getByText("Admin workspace")).toBeInTheDocument();
    expect(screen.queryByText("Loading workspace…")).toBeNull();
  });

  it("shows spinner only while initializing", () => {
    authState = {
      ...authState,
      isInitializingSession: true,
      isAuthenticated: false,
      status: "unauthenticated",
    };
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>Admin workspace</div>
      </AppShell>,
    );
    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();
  });

  it("profile/org/permission failure exits loading with actionable error", () => {
    authState = {
      isHydrated: true,
      isInitializingSession: false,
      isAuthenticated: false,
      status: "unauthenticated",
      error: "Unable to load profile",
    };
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>Admin workspace</div>
      </AppShell>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Unable to load profile");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByText("Loading workspace…")).toBeNull();
  });

  it("timeout error exits loading with controlled error screen", () => {
    authState = {
      isHydrated: true,
      isInitializingSession: false,
      isAuthenticated: false,
      status: "unauthenticated",
      error: "Session restore timed out",
    };
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>hidden</div>
      </AppShell>,
    );
    expect(
      screen.getByRole("heading", { name: /Unable to load workspace/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(/timed out/i);
  });
});
