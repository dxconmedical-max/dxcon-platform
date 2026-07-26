import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();

type Gate = {
  isHydrated: boolean;
  bootstrapPhase: "idle" | "restoring" | "authenticated" | "anonymous" | "failed";
  isInitializingSession: boolean;
  isBootstrapping: boolean;
  isAuthenticated: boolean;
  status: "authenticated" | "unauthenticated";
  error: string | null;
  capabilities: Record<string, unknown> | null;
  role: string | null;
};

let authState: Gate = {
  isHydrated: true,
  bootstrapPhase: "authenticated",
  isInitializingSession: false,
  isBootstrapping: false,
  isAuthenticated: true,
  status: "authenticated",
  error: null,
  capabilities: {
    workspace: "/app/admin",
    permissions: ["*"],
    features: [],
    user: { id: "1", email: "a@b.com", role: "ADMIN" },
  },
  role: "ADMIN",
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
    accessToken: "tok",
    refreshToken: "ref",
    workspacePath: "/app/admin",
    can: () => true,
    canAny: () => true,
    canAll: () => true,
    hasFeature: () => true,
    isWorkspace: () => true,
    isOrganizationType: () => true,
  }),
}));

const storeState: {
  restoreSession: ReturnType<typeof vi.fn>;
  logout: ReturnType<typeof vi.fn>;
  clearTransientFlags: ReturnType<typeof vi.fn>;
  bootstrapPhase: "idle" | "restoring" | "authenticated" | "anonymous" | "failed";
  status: "authenticated" | "unauthenticated";
  isHydrated: boolean;
  accessToken: string | null;
  capabilities: Record<string, unknown> | null;
  role: string | null;
  error: string | null;
  isInitializingSession: boolean;
} = {
  restoreSession: vi.fn(),
  logout: vi.fn(async () => undefined),
  clearTransientFlags: vi.fn(),
  bootstrapPhase: "authenticated",
  status: "authenticated",
  isHydrated: true,
  accessToken: "tok",
  capabilities: authState.capabilities,
  role: "ADMIN",
  error: null,
  isInitializingSession: false,
};

vi.mock("@/stores/authStore", () => {
  const isBootstrapPending = (phase: string) =>
    phase === "idle" || phase === "restoring";
  const useAuthStore = Object.assign(
    (selector?: (s: typeof storeState) => unknown) =>
      selector ? selector(storeState) : storeState,
    {
      setState: (partial: Partial<typeof storeState>) => {
        Object.assign(storeState, partial);
      },
      getState: () => storeState,
    },
  );
  return {
    useAuthStore,
    isBootstrapPending,
    isBootstrapTerminal: (phase: string) =>
      phase === "authenticated" ||
      phase === "anonymous" ||
      phase === "failed",
  };
});

vi.mock("@/components/layout/Header", () => ({
  Header: ({ title }: { title: string }) => <div>{title}</div>,
  MobileNav: () => null,
}));

vi.mock("@/components/layout/Sidebar", () => ({
  Sidebar: () => <nav>Sidebar</nav>,
}));

import {
  APP_SHELL_BOOTSTRAP_TIMEOUT_MS,
  AppShell,
} from "./AppShell";

describe("AppShell after single-owner bootstrap", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  beforeEach(() => {
    replace.mockReset();
    storeState.bootstrapPhase = "authenticated";
    storeState.status = "authenticated";
    storeState.isHydrated = true;
    storeState.accessToken = "tok";
    storeState.capabilities = authState.capabilities;
    storeState.role = "ADMIN";
    storeState.error = null;
    storeState.isInitializingSession = false;
    authState = {
      isHydrated: true,
      bootstrapPhase: "authenticated",
      isInitializingSession: false,
      isBootstrapping: false,
      isAuthenticated: true,
      status: "authenticated",
      error: null,
      capabilities: {
        workspace: "/app/admin",
        permissions: ["*"],
        features: [],
        user: { id: "1", email: "a@b.com", role: "ADMIN" },
      },
      role: "ADMIN",
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
    expect(screen.queryByText("Loading workspace…")).not.toBeInTheDocument();
  });

  it("shows spinner while bootstrapPhase is restoring", () => {
    authState = {
      ...authState,
      bootstrapPhase: "restoring",
      isBootstrapping: true,
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
      isBootstrapping: false,
      isAuthenticated: false,
      status: "unauthenticated",
      error: "Session restore timed out",
      capabilities: null,
      role: null,
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

  it("bounded bootstrap timeout replaces indefinite spinner with diagnostics", () => {
    vi.useFakeTimers();
    authState = {
      ...authState,
      bootstrapPhase: "restoring",
      isBootstrapping: true,
      isAuthenticated: false,
      status: "unauthenticated",
      error: null,
      capabilities: null,
    };
    storeState.bootstrapPhase = "restoring";
    storeState.status = "unauthenticated";
    storeState.capabilities = null;
    storeState.accessToken = "tok";

    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>x</div>
      </AppShell>,
    );
    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(APP_SHELL_BOOTSTRAP_TIMEOUT_MS + 50);
    });

    expect(
      screen.getByRole("heading", { name: /Unable to load workspace/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(/timed out/i);
    expect(screen.getByText(/phase=failed/)).toBeInTheDocument();
    expect(screen.queryByText("Loading workspace…")).not.toBeInTheDocument();
  });

  it("authenticated without capabilities shows diagnostic, not spinner", () => {
    authState = {
      ...authState,
      capabilities: null,
      bootstrapPhase: "authenticated",
      isBootstrapping: false,
      isAuthenticated: true,
      status: "authenticated",
    };
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>Admin workspace</div>
      </AppShell>,
    );
    expect(
      screen.getByRole("heading", { name: /Permissions not loaded/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Loading workspace…")).not.toBeInTheDocument();
  });

  it("shows Redirecting only for terminal anonymous", () => {
    authState = {
      ...authState,
      bootstrapPhase: "anonymous",
      isBootstrapping: false,
      isAuthenticated: false,
      status: "unauthenticated",
      error: null,
      capabilities: null,
      role: null,
    };
    storeState.bootstrapPhase = "anonymous";
    storeState.status = "unauthenticated";
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>x</div>
      </AppShell>,
    );
    expect(screen.getByText("Redirecting to sign in…")).toBeInTheDocument();
  });

  it("does not show Redirecting when status is authenticated with stale anonymous phase", () => {
    authState = {
      ...authState,
      bootstrapPhase: "anonymous",
      isBootstrapping: false,
      isAuthenticated: true,
      status: "authenticated",
      error: null,
      capabilities: {
        workspace: "/app/admin",
        permissions: ["*"],
        features: [],
        user: { id: "1", email: "a@b.com", role: "SUPER_ADMIN" },
      },
      role: "SUPER_ADMIN",
    };
    storeState.bootstrapPhase = "anonymous";
    storeState.status = "authenticated";
    storeState.capabilities = authState.capabilities;
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>Admin workspace</div>
      </AppShell>,
    );
    expect(screen.queryByText("Redirecting to sign in…")).not.toBeInTheDocument();
    expect(screen.getByText("Administration")).toBeInTheDocument();
    expect(screen.getByText("Admin workspace")).toBeInTheDocument();
  });

  it("keeps spinner while restoring even when isAuthenticated is false", () => {
    authState = {
      ...authState,
      bootstrapPhase: "restoring",
      isBootstrapping: true,
      isAuthenticated: false,
      status: "unauthenticated",
      error: null,
      capabilities: null,
    };
    storeState.bootstrapPhase = "restoring";
    render(
      <AppShell title="Administration" workspacePath="/app/admin">
        <div>x</div>
      </AppShell>,
    );
    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();
    expect(
      screen.queryByText("Redirecting to sign in…"),
    ).not.toBeInTheDocument();
  });
});
