import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  usePathname: () => "/app/admin",
}));

vi.mock("@/lib/cookies", () => ({
  setAuthCookies: vi.fn(),
  clearAuthCookies: vi.fn(),
}));

const fetchMe = vi.fn();
const fetchCapabilities = vi.fn();
const loginRequest = vi.fn();
const logoutRequest = vi.fn();
const refreshAccessToken = vi.fn();
const switchOrganization = vi.fn();

vi.mock("@/services/auth", () => ({
  fetchMe: (...a: unknown[]) => fetchMe(...a),
  fetchCapabilities: (...a: unknown[]) => fetchCapabilities(...a),
  login: (...a: unknown[]) => loginRequest(...a),
  logout: (...a: unknown[]) => logoutRequest(...a),
  refreshAccessToken: (...a: unknown[]) => refreshAccessToken(...a),
  switchOrganization: (...a: unknown[]) => switchOrganization(...a),
}));

import { AuthProvider } from "@/components/providers/AuthProvider";
import { AppShell } from "@/components/layout/AppShell";
import {
  resetAuthRestoreForTests,
  useAuthStore,
} from "@/stores/authStore";
import { buildNavItems } from "@/lib/navigation";

const capsPayload = {
  user: { id: "1", email: "admin@dxcon.test", role: "ADMIN" },
  organization: null,
  membership: {
    membership_id: "m1",
    organization_id: "org1",
    role_code: "ADMIN",
    membership_status: "active",
  },
  workspace: "/app/admin",
  default_workspace: "/app/admin",
  permissions: ["*"],
  features: [],
};

async function resetStore() {
  sessionStorage.clear();
  resetAuthRestoreForTests();
  await useAuthStore.persist.rehydrate();
  useAuthStore.setState({
    status: "unauthenticated",
    bootstrapPhase: "idle",
    user: null,
    role: null,
    accessToken: null,
    refreshToken: null,
    tokenExpiresAt: null,
    memberships: [],
    activeOrganizationId: null,
    capabilities: null,
    error: null,
    isHydrated: true,
    isInitializingSession: false,
    isSubmittingLogin: false,
    isRefreshingSession: false,
  });
}

describe("Admin shell after restoreSession succeeds", () => {
  beforeEach(async () => {
    await resetStore();
    replace.mockReset();
    fetchMe.mockReset();
    fetchCapabilities.mockReset();
    loginRequest.mockReset();
    logoutRequest.mockReset();
    refreshAccessToken.mockReset();
    switchOrganization.mockReset();
  });

  afterEach(() => {
    cleanup();
    resetAuthRestoreForTests();
  });

  it("renders admin shell once restore completes (no spinner)", async () => {
    fetchMe.mockResolvedValue({
      user: { id: "1", email: "admin@dxcon.test", role: "ADMIN" },
      active_organization_id: "org1",
      memberships: [
        {
          membership_id: "m1",
          organization_id: "org1",
          organization_name: "Org",
          organization_type: "DXCON_INTERNAL",
          organization_code: "O1",
          organization_status: "active",
          role_code: "ADMIN",
          membership_status: "active",
          default_workspace: "/app/admin",
        },
      ],
      requires_organization_selection: false,
    });
    fetchCapabilities.mockResolvedValue(capsPayload);

    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "idle",
      accessToken: "access",
      refreshToken: "refresh",
      user: { id: "1", email: "admin@dxcon.test", role: "ADMIN" },
      role: "ADMIN",
      status: "unauthenticated",
      isInitializingSession: true,
    });

    render(
      <AuthProvider>
        <AppShell title="Administration" workspacePath="/app/admin">
          <div>Admin workspace</div>
        </AppShell>
      </AuthProvider>,
    );

    expect(screen.getByText("Loading workspace…")).toBeInTheDocument();

    await waitFor(() => {
      expect(useAuthStore.getState().bootstrapPhase).toBe("authenticated");
      expect(useAuthStore.getState().status).toBe("authenticated");
    });

    await waitFor(() => {
      expect(screen.getAllByText("Administration").length).toBeGreaterThan(0);
      expect(screen.getByText("Admin workspace")).toBeInTheDocument();
    });
    expect(screen.queryByText("Loading workspace…")).not.toBeInTheDocument();
    expect(fetchMe).toHaveBeenCalledTimes(1);
  });

  it("login then shell render does not re-enter restoring spinner", async () => {
    loginRequest.mockResolvedValue({
      success: true,
      token: "access",
      access_token: "access",
      refresh_token: "refresh",
      email: "admin@dxcon.test",
      role: "ADMIN",
      user: { id: "1", email: "admin@dxcon.test", role: "ADMIN" },
    });
    fetchMe.mockResolvedValue({
      user: { id: "1", email: "admin@dxcon.test", role: "ADMIN" },
      active_organization_id: "org1",
      memberships: [
        {
          membership_id: "m1",
          organization_id: "org1",
          organization_name: "Org",
          organization_type: "DXCON_INTERNAL",
          organization_code: "O1",
          organization_status: "active",
          role_code: "ADMIN",
          membership_status: "active",
          default_workspace: "/app/admin",
        },
      ],
      requires_organization_selection: false,
    });
    fetchCapabilities.mockResolvedValue({
      ...capsPayload,
      user: undefined,
    });

    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "authenticated",
      status: "unauthenticated",
    });

    await act(async () => {
      await useAuthStore.getState().login("admin@dxcon.test", "secret");
    });

    expect(useAuthStore.getState().bootstrapPhase).toBe("authenticated");
    expect(useAuthStore.getState().status).toBe("authenticated");
    expect(useAuthStore.getState().capabilities?.user?.role).toBe("ADMIN");

    render(
      <AuthProvider>
        <AppShell title="Administration" workspacePath="/app/admin">
          <div>Admin workspace</div>
        </AppShell>
      </AuthProvider>,
    );

    expect(screen.getAllByText("Administration").length).toBeGreaterThan(0);
    expect(screen.queryByText("Loading workspace…")).not.toBeInTheDocument();
  });

  it("buildNavItems does not throw when capabilities.user is missing", () => {
    expect(() =>
      buildNavItems({
        workspace: "/app/admin",
        default_workspace: "/app/admin",
        permissions: ["*"],
        features: [],
        organization: null,
        membership: {
          membership_id: null,
          organization_id: null,
          role_code: null,
          membership_status: null,
        },
      }),
    ).not.toThrow();
  });

  it("logout leaves bootstrap anonymous so shell does not spin forever", async () => {
    useAuthStore.setState({
      status: "authenticated",
      bootstrapPhase: "authenticated",
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "a@b.com", role: "ADMIN" },
      role: "ADMIN",
      capabilities: capsPayload as never,
      isHydrated: true,
    });
    await useAuthStore.getState().logout();
    const s = useAuthStore.getState();
    expect(s.status).toBe("unauthenticated");
    expect(s.bootstrapPhase).toBe("anonymous");
    expect(s.accessToken).toBeNull();
  });
});
