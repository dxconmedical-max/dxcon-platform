import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
const login = vi.fn();
const clearError = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    login,
    error: null,
    clearError,
    isAuthenticated: false,
    workspacePath: "/app",
    isHydrated: true,
    // Session bootstrap still reports loading — must not drive the submit button.
    status: "loading",
    isLoading: true,
  }),
}));

vi.mock("@/lib/constants", () => ({
  DEMO_MODE: false,
}));

import LoginPage from "./page";

function submitButton(name: "Sign in" | "Signing in...") {
  return screen.getByRole("button", { name: new RegExp(`^${name}$`) });
}

describe("LoginPage submit loading state", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    replace.mockReset();
    login.mockReset();
    clearError.mockReset();
  });

  it("shows Sign in on initial render and is not in a loading state", () => {
    render(<LoginPage />);
    const button = submitButton("Sign in");
    expect(button).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Signing in\.\.\.$/ })).not.toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  it("enables submission when email and password are valid", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "admin@dxcon.com.vn");
    await user.type(screen.getByLabelText("Password"), "secret");

    expect(submitButton("Sign in")).toBeEnabled();
  });

  it("shows Signing in... while login is in progress", async () => {
    const user = userEvent.setup();
    let resolveLogin: (value: { redirect: string }) => void = () => undefined;
    login.mockImplementation(
      () =>
        new Promise<{ redirect: string }>((resolve) => {
          resolveLogin = resolve;
        }),
    );

    render(<LoginPage />);
    await user.type(screen.getByLabelText("Email"), "admin@dxcon.com.vn");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(submitButton("Sign in"));

    expect(await screen.findByRole("button", { name: /^Signing in\.\.\.$/ })).toBeDisabled();

    resolveLogin({ redirect: "/app" });
    await waitFor(() => {
      expect(submitButton("Sign in")).toBeInTheDocument();
    });
  });

  it("restores Sign in after a failed login", async () => {
    const user = userEvent.setup();
    login.mockRejectedValue(new Error("Invalid credentials"));

    render(<LoginPage />);
    await user.type(screen.getByLabelText("Email"), "admin@dxcon.com.vn");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(submitButton("Sign in"));

    await waitFor(() => {
      expect(submitButton("Sign in")).toBeEnabled();
    });
    expect(screen.queryByRole("button", { name: /^Signing in\.\.\.$/ })).not.toBeInTheDocument();
  });
});
