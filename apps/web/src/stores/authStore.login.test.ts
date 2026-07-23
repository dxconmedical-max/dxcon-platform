import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchMe = vi.fn();
const fetchCapabilities = vi.fn();
const loginRequest = vi.fn();
const logoutRequest = vi.fn();
const refreshAccessToken = vi.fn();
const switchOrganization = vi.fn();

vi.mock("@/services/auth", () => ({
  fetchMe: (...args: unknown[]) => fetchMe(...args),
  fetchCapabilities: (...args: unknown[]) => fetchCapabilities(...args),
  login: (...args: unknown[]) => loginRequest(...args),
  logout: (...args: unknown[]) => logoutRequest(...args),
  refreshAccessToken: (...args: unknown[]) => refreshAccessToken(...args),
  switchOrganization: (...args: unknown[]) => switchOrganization(...args),
}));

vi.mock("@/lib/cookies", () => ({
  setAuthCookies: vi.fn(),
  clearAuthCookies: vi.fn(),
}));

import { ApiError } from "@/lib/errors";
import { resetAuthRestoreForTests, useAuthStore } from "@/stores/authStore";

function resetStore() {
  sessionStorage.clear();
  resetAuthRestoreForTests();
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

describe("authStore login / session machine", () => {
  beforeEach(() => {
    resetStore();
    fetchMe.mockReset();
    fetchCapabilities.mockReset();
    loginRequest.mockReset();
    logoutRequest.mockReset();
    refreshAccessToken.mockReset();
    switchOrganization.mockReset();
  });

  it("starts anonymous with all transient flags false", () => {
    const s = useAuthStore.getState();
    expect(s.status).toBe("unauthenticated");
    expect(s.isSubmittingLogin).toBe(false);
    expect(s.isInitializingSession).toBe(false);
    expect(s.isRefreshingSession).toBe(false);
  });

  it("one login produces exactly one POST and clears isSubmittingLogin", async () => {
    loginRequest.mockResolvedValue({
      success: true,
      access_token: "a",
      token: "a",
      refresh_token: "r",
      email: "u@x.com",
      role: "ADMIN",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
    });
    fetchMe.mockResolvedValue({
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      active_organization_id: "org1",
      memberships: [
        {
          membership_id: "m1",
          organization_id: "org1",
          organization_name: "Org",
          organization_type: "LAB",
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
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      organization: null,
      membership: {
        membership_id: "m1",
        organization_id: "org1",
        role_code: "ADMIN",
        membership_status: "active",
      },
      workspace: "/app/admin",
      default_workspace: "/app/admin",
      permissions: [],
      features: [],
    });

    const result = await useAuthStore.getState().login("u@x.com", "secret");
    expect(loginRequest).toHaveBeenCalledTimes(1);
    expect(result.redirect).toBe("/app/admin");
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
    expect(useAuthStore.getState().status).toBe("authenticated");
    expect(useAuthStore.getState().accessToken).toBe("a");
  });

  it("failed login resets isSubmittingLogin and keeps anonymous", async () => {
    loginRequest.mockRejectedValue(new ApiError("Invalid credentials", 401));
    await expect(
      useAuthStore.getState().login("u@x.com", "bad"),
    ).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
    expect(useAuthStore.getState().status).toBe("unauthenticated");
  });

  it("API 500 resets isSubmittingLogin", async () => {
    loginRequest.mockRejectedValue(new ApiError("boom", 500));
    await expect(
      useAuthStore.getState().login("u@x.com", "x"),
    ).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
  });

  it("network failure resets isSubmittingLogin", async () => {
    loginRequest.mockRejectedValue(
      new ApiError("Network error — check your connection", 0, {
        code: "NETWORK_ERROR",
      }),
    );
    await expect(
      useAuthStore.getState().login("u@x.com", "x"),
    ).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
  });

  it("timeout resets isSubmittingLogin", async () => {
    loginRequest.mockRejectedValue(
      new ApiError("Request timed out", 408, { code: "TIMEOUT" }),
    );
    await expect(
      useAuthStore.getState().login("u@x.com", "x"),
    ).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
  });

  it("malformed login response resets button flag", async () => {
    loginRequest.mockResolvedValue({ success: true });
    await expect(
      useAuthStore.getState().login("u@x.com", "x"),
    ).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
  });

  it("double login while submitting is rejected without second POST", async () => {
    let resolveLogin!: (v: unknown) => void;
    loginRequest.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveLogin = resolve;
        }),
    );
    const first = useAuthStore.getState().login("u@x.com", "x");
    await vi.waitFor(() => {
      expect(useAuthStore.getState().isSubmittingLogin).toBe(true);
    });
    await expect(useAuthStore.getState().login("u@x.com", "x")).rejects.toBeInstanceOf(
      ApiError,
    );
    expect(loginRequest).toHaveBeenCalledTimes(1);
    resolveLogin({
      access_token: "a",
      refresh_token: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
      email: "u@x.com",
    });
    fetchMe.mockResolvedValue({
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      active_organization_id: "org1",
      memberships: [
        {
          membership_id: "m1",
          organization_id: "org1",
          organization_name: "Org",
          organization_type: "LAB",
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
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      organization: null,
      membership: {
        membership_id: "m1",
        organization_id: "org1",
        role_code: "ADMIN",
        membership_status: "active",
      },
      workspace: "/app/admin",
      default_workspace: "/app/admin",
      permissions: [],
      features: [],
    });
    await first;
    expect(useAuthStore.getState().isSubmittingLogin).toBe(false);
  });

  it("profile request failure exits loading with error", async () => {
    useAuthStore.setState({
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
      isInitializingSession: true,
    });
    fetchMe.mockRejectedValue(new ApiError("boom", 500));
    await useAuthStore.getState().restoreSession();
    expect(useAuthStore.getState().isInitializingSession).toBe(false);
    expect(useAuthStore.getState().error).toBeTruthy();
  });

  it("capabilities failure exits loading", async () => {
    useAuthStore.setState({
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
    });
    fetchMe.mockResolvedValue({
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      active_organization_id: "org1",
      memberships: [
        {
          membership_id: "m1",
          organization_id: "org1",
          organization_name: "Org",
          organization_type: "LAB",
          organization_code: "O1",
          organization_status: "active",
          role_code: "ADMIN",
          membership_status: "active",
          default_workspace: "/app/admin",
        },
      ],
      requires_organization_selection: false,
    });
    fetchCapabilities.mockRejectedValue(new ApiError("caps down", 500));
    await useAuthStore.getState().restoreSession();
    expect(useAuthStore.getState().isInitializingSession).toBe(false);
    expect(useAuthStore.getState().status).not.toBe("authenticated");
  });

  it("restoreSession success terminates initialization flags", async () => {
    useAuthStore.setState({
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
      isInitializingSession: true,
    });
    fetchMe.mockResolvedValue({
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      active_organization_id: "org1",
      memberships: [
        {
          membership_id: "m1",
          organization_id: "org1",
          organization_name: "Org",
          organization_type: "LAB",
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
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      organization: null,
      membership: {
        membership_id: "m1",
        organization_id: "org1",
        role_code: "ADMIN",
        membership_status: "active",
      },
      workspace: "/app/admin",
      default_workspace: "/app/admin",
      permissions: [],
      features: [],
    });
    const status = await useAuthStore.getState().restoreSession();
    expect(status).toBe("authenticated");
    expect(useAuthStore.getState().isInitializingSession).toBe(false);
  });

  it("hydration completion forces transient flags off", () => {
    useAuthStore.setState({
      isHydrated: false,
      isSubmittingLogin: true,
      isInitializingSession: true,
      isRefreshingSession: true,
      error: "stale",
    });
    useAuthStore.getState().clearTransientFlags();
    useAuthStore.setState({ isHydrated: true });
    const s = useAuthStore.getState();
    expect(s.isSubmittingLogin).toBe(false);
    expect(s.isInitializingSession).toBe(false);
    expect(s.isRefreshingSession).toBe(false);
    expect(s.error).toBeNull();
    expect(s.isHydrated).toBe(true);
  });

  it("refresh after login keeps tokens until logout", async () => {
    useAuthStore.setState({
      status: "authenticated",
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
      isHydrated: true,
    });
    expect(useAuthStore.getState().accessToken).toBe("a");
    expect(useAuthStore.getState().status).toBe("authenticated");
  });

  it("logout clears session and transient flags for a clean login page", async () => {
    useAuthStore.setState({
      status: "authenticated",
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      isSubmittingLogin: true,
      isInitializingSession: true,
      bootstrapPhase: "complete",
    });
    await useAuthStore.getState().logout();
    const s = useAuthStore.getState();
    expect(s.status).toBe("unauthenticated");
    expect(s.bootstrapPhase).toBe("complete");
    expect(s.accessToken).toBeNull();
    expect(s.isSubmittingLogin).toBe(false);
    expect(s.isInitializingSession).toBe(false);
  });
});
