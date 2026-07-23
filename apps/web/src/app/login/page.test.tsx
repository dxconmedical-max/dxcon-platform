import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

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
    isInitializing: true,
    isLoading: true,
  }),
}));

vi.mock("@/lib/constants", () => ({
  DEMO_MODE: false,
}));

import LoginPage from "./page";

function submitButton() {
  const button = document.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (!button) throw new Error("submit button not found");
  return button;
}

function fillCredentials() {
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "user@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "secret" },
  });
}

describe("LoginPage submit loading state", () => {
  beforeEach(() => {
    replace.mockReset();
    login.mockReset();
    clearError.mockReset();
  });

  it("fresh page renders Sign in, not Signing in...", () => {
    render(<LoginPage />);
    const button = submitButton();
    expect(button).toHaveTextContent("Sign in");
    expect(button).not.toHaveTextContent("Signing in...");
  });

  it("stale auth isLoading=true does not lock the submit label", () => {
    render(<LoginPage />);
    expect(submitButton()).toHaveTextContent("Sign in");
  });

  it("enables Sign in once email and password are valid", () => {
    render(<LoginPage />);
    expect(submitButton()).toBeDisabled();
    fillCredentials();
    expect(submitButton()).toBeEnabled();
  });

  it("clicking submit creates exactly one login call", async () => {
    login.mockResolvedValue({ redirect: "/app" });
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(login).toHaveBeenCalledTimes(1);
    });
    expect(login).toHaveBeenCalledWith("user@example.com", "secret", false);
  });

  it("successful login redirects", async () => {
    login.mockResolvedValue({ redirect: "/app/admin" });
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith("/app/admin");
    });
  });

  it("failed login resets the button", async () => {
    login.mockRejectedValue(new ApiError("Invalid email or password.", 401));
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(submitButton()).toBeEnabled();
    });
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid email or password.");
  });

  it("timeout resets the button and shows network message", async () => {
    login.mockRejectedValue(
      new ApiError("Request timed out", 408, { code: "TIMEOUT" }),
    );
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(submitButton()).toBeEnabled();
    });
    expect(screen.getByRole("alert")).toHaveTextContent(/Network error/);
  });

  it("preserves 500 message", async () => {
    login.mockRejectedValue(new ApiError("Upstream lab gateway failed", 500));
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Upstream lab gateway failed",
      );
    });
  });
});
