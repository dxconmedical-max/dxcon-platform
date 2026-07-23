import { act, cleanup, render, waitFor } from "@testing-library/react";
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
import { useRequireAuth } from "@/hooks/useAuth";
import {
  resetAuthRestoreForTests,
  useAuthStore,
} from "@/stores/authStore";

const me = {
  user: { id: "1", email: "admin@dxcon.test", role: "SUPER_ADMIN" },
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
};

const caps = {
  user: { id: "1", email: "admin@dxcon.test", role: "SUPER_ADMIN" },
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

function GuardProbe() {
  useRequireAuth("/app/admin");
  return <div>guard</div>;
}

describe("Gate 1 auth regression", () => {
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

  it("restoreSession with tokens reaches authenticated and calls /me", async () => {
    fetchMe.mockResolvedValue(me);
    fetchCapabilities.mockResolvedValue(caps);
    useAuthStore.setState({
      accessToken: "access",
      refreshToken: "refresh",
      user: me.user,
      role: "SUPER_ADMIN",
      bootstrapPhase: "idle",
      isHydrated: true,
    });

    const status = await useAuthStore.getState().restoreSession();
    expect(status).toBe("authenticated");
    expect(fetchMe).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState().bootstrapPhase).toBe("authenticated");
    expect(useAuthStore.getState().status).toBe("authenticated");
  });

  it("login → authenticated → AppShell renders admin (no redirect to login)", async () => {
    loginRequest.mockResolvedValue({
      success: true,
      token: "access",
      access_token: "access",
      refresh_token: "refresh",
      email: "admin@dxcon.test",
      role: "SUPER_ADMIN",
      user: me.user,
    });
    fetchMe.mockResolvedValue(me);
    fetchCapabilities.mockResolvedValue(caps);

    // /login hydrate left phase anonymous before credentials submit.
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "anonymous",
      status: "unauthenticated",
    });

    await act(async () => {
      await useAuthStore.getState().login("admin@dxcon.test", "secret");
    });

    expect(useAuthStore.getState().status).toBe("authenticated");
    expect(useAuthStore.getState().bootstrapPhase).toBe("authenticated");

    render(
      <AuthProvider>
        <AppShell title="Administration" workspacePath="/app/admin">
          <div>Admin workspace</div>
        </AppShell>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(document.body.textContent).toContain("Administration");
      expect(document.body.textContent).toContain("Admin workspace");
    });
    expect(replace).not.toHaveBeenCalledWith("/login");
    expect(document.body.textContent).not.toContain("Redirecting to sign in");
  });

  it("anonymous redirect: guard sends unauthenticated terminal users to /login", () => {
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "anonymous",
      status: "unauthenticated",
      accessToken: null,
      user: null,
    });
    render(<GuardProbe />);
    expect(replace).toHaveBeenCalledWith("/login");
  });

  it("authenticated redirect: guard does not bounce authenticated users to /login", () => {
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "authenticated",
      status: "authenticated",
      accessToken: "access",
      user: me.user,
      role: "SUPER_ADMIN",
      capabilities: caps as never,
    });
    render(<GuardProbe />);
    expect(replace).not.toHaveBeenCalled();
  });

  it("logout clears session to anonymous so a later login can proceed", async () => {
    useAuthStore.setState({
      status: "authenticated",
      bootstrapPhase: "authenticated",
      accessToken: "access",
      refreshToken: "refresh",
      user: me.user,
      role: "SUPER_ADMIN",
      capabilities: caps as never,
      isHydrated: true,
    });
    await useAuthStore.getState().logout();
    const s = useAuthStore.getState();
    expect(s.status).toBe("unauthenticated");
    expect(s.bootstrapPhase).toBe("anonymous");
    expect(s.accessToken).toBeNull();
    expect(s.capabilities).toBeNull();
  });
});
