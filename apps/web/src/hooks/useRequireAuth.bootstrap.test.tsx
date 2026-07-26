import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  usePathname: () => "/app/admin",
}));

import { useRequireAuth } from "@/hooks/useAuth";
import {
  resetAuthRestoreForTests,
  useAuthStore,
} from "@/stores/authStore";

function GuardProbe() {
  useRequireAuth("/app/admin");
  return <div>guard-mounted</div>;
}

describe("useRequireAuth waits for bootstrap", () => {
  beforeEach(() => {
    replace.mockReset();
    resetAuthRestoreForTests();
    sessionStorage.clear();
    useAuthStore.setState({
      status: "unauthenticated",
      bootstrapPhase: "idle",
      user: null,
      role: null,
      accessToken: null,
      refreshToken: null,
      capabilities: null,
      error: null,
      isHydrated: true,
      isInitializingSession: true,
      isSubmittingLogin: false,
      isRefreshingSession: false,
      memberships: [],
      activeOrganizationId: null,
    });
  });

  afterEach(() => {
    cleanup();
    resetAuthRestoreForTests();
  });

  it("does not redirect while bootstrapPhase is restoring (even if status is unauthenticated)", () => {
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "restoring",
      status: "unauthenticated",
      accessToken: "tok",
      user: { id: "1", email: "a@b.com", role: "ADMIN" },
      role: "ADMIN",
    });

    render(<GuardProbe />);

    expect(replace).not.toHaveBeenCalled();
    expect(screen.getByText("guard-mounted")).toBeInTheDocument();
  });

  it("does not redirect while bootstrapPhase is idle", () => {
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "idle",
      status: "unauthenticated",
      accessToken: "tok",
      user: { id: "1", email: "a@b.com", role: "ADMIN" },
    });

    render(<GuardProbe />);
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirects only after terminal anonymous", () => {
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

  it("does not redirect when status is authenticated even if phase is still anonymous (login race)", () => {
    // Cookies + status flip one render before bootstrapPhase catches up.
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "anonymous",
      status: "authenticated",
      accessToken: "tok",
      user: { id: "1", email: "a@b.com", role: "SUPER_ADMIN" },
      role: "SUPER_ADMIN",
      capabilities: {
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
        user: { id: "1", email: "a@b.com", role: "SUPER_ADMIN" },
      },
    });

    render(<GuardProbe />);
    expect(replace).not.toHaveBeenCalled();
  });

  it("does not redirect when terminal authenticated", () => {
    useAuthStore.setState({
      isHydrated: true,
      bootstrapPhase: "authenticated",
      status: "authenticated",
      accessToken: "tok",
      user: { id: "1", email: "a@b.com", role: "ADMIN" },
      role: "ADMIN",
      capabilities: {
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
        user: { id: "1", email: "a@b.com", role: "ADMIN" },
      },
    });

    render(<GuardProbe />);
    expect(replace).not.toHaveBeenCalled();
  });
});
