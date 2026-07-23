import { act, cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

vi.mock("@/lib/cookies", () => ({
  setAuthCookies: vi.fn(),
  clearAuthCookies: vi.fn(),
}));

import { AuthProvider } from "@/components/providers/AuthProvider";
import {
  resetAuthRestoreForTests,
  useAuthStore,
} from "@/stores/authStore";

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

const mePayload = {
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
};

const capsPayload = {
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
};

describe("restoreSession single-flight / idempotency", () => {
  beforeEach(async () => {
    await resetStore();
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

  it("shares one in-flight promise across concurrent callers", async () => {
    let resolveMe!: (v: unknown) => void;
    fetchMe.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveMe = resolve;
        }),
    );
    fetchCapabilities.mockResolvedValue(capsPayload);

    useAuthStore.setState({
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
      bootstrapPhase: "idle",
      isHydrated: true,
    });

    const p1 = useAuthStore.getState().restoreSession();
    const p2 = useAuthStore.getState().restoreSession();
    expect(p1).toBe(p2);
    expect(fetchMe).toHaveBeenCalledTimes(1);

    resolveMe(mePayload);
    await p1;
    expect(useAuthStore.getState().bootstrapPhase).toBe("complete");
    expect(useAuthStore.getState().status).toBe("authenticated");
  });

  it("already-complete session does not call APIs again", async () => {
    useAuthStore.setState({
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
      status: "authenticated",
      bootstrapPhase: "complete",
      capabilities: capsPayload as never,
      isHydrated: true,
    });
    const status = await useAuthStore.getState().restoreSession();
    expect(status).toBe("authenticated");
    expect(fetchMe).not.toHaveBeenCalled();
  });

  it("AuthProvider mounts restore once", async () => {
    fetchMe.mockResolvedValue(mePayload);
    fetchCapabilities.mockResolvedValue(capsPayload);

    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "idle",
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
    });

    await act(async () => {
      render(
        <AuthProvider>
          <div>child</div>
        </AuthProvider>,
      );
    });

    await waitFor(() => {
      expect(useAuthStore.getState().bootstrapPhase).toBe("complete");
      expect(useAuthStore.getState().status).toBe("authenticated");
    });
    expect(fetchMe).toHaveBeenCalledTimes(1);
  });

  it("updating session fields after complete does not re-trigger restore", async () => {
    fetchMe.mockResolvedValue(mePayload);
    fetchCapabilities.mockResolvedValue(capsPayload);

    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "idle",
      accessToken: "a",
      refreshToken: "r",
      user: { id: "1", email: "u@x.com", role: "ADMIN" },
      role: "ADMIN",
    });

    render(
      <AuthProvider>
        <div>child</div>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(useAuthStore.getState().status).toBe("authenticated");
    });
    const calls = fetchMe.mock.calls.length;

    act(() => {
      useAuthStore.setState({ role: "SUPER_ADMIN" });
    });

    await act(async () => {
      await Promise.resolve();
    });
    expect(fetchMe.mock.calls.length).toBe(calls);
  });
});
