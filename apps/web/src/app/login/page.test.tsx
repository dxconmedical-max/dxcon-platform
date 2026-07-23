import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";

const replace = vi.fn();
const login = vi.fn();
const clearError = vi.fn();
let isSubmittingLogin = false;

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    login: async (...args: unknown[]) => {
      isSubmittingLogin = true;
      try {
        return await login(...args);
      } finally {
        isSubmittingLogin = false;
      }
    },
    error: null,
    clearError,
    isAuthenticated: false,
    workspacePath: "/app",
    isHydrated: true,
    isInitializingSession: true,
    isSubmittingLogin,
    isRefreshingSession: false,
    status: "unauthenticated",
    bootstrapPhase: "anonymous",
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
    isSubmittingLogin = false;
  });

  it("fresh anonymous visit renders Sign in, never Signing in...", () => {
    render(<LoginPage />);
    const button = submitButton();
    expect(button).toHaveTextContent("Sign in");
    expect(button).not.toHaveTextContent("Signing in...");
  });

  it("session initialization flags do not lock the submit label", () => {
    render(<LoginPage />);
    expect(submitButton()).toHaveTextContent("Sign in");
  });

  it("enables Sign in once email and password are valid", () => {
    render(<LoginPage />);
    expect(submitButton()).toBeDisabled();
    fillCredentials();
    expect(submitButton()).toBeEnabled();
  });

  it("one submit / double submit creates exactly one login call", async () => {
    login.mockResolvedValue({ redirect: "/app" });
    render(<LoginPage />);
    fillCredentials();
    const form = submitButton().closest("form")!;
    fireEvent.submit(form);
    fireEvent.submit(form);
    await waitFor(() => {
      expect(login).toHaveBeenCalledTimes(1);
    });
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

  it("invalid credentials show auth error and reset the button", async () => {
    login.mockRejectedValue(new ApiError("Invalid credentials", 401));
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(submitButton()).toBeEnabled();
    });
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid email or password.");
  });

  it("API 500 resets the button and preserves message", async () => {
    login.mockRejectedValue(new ApiError("Upstream lab gateway failed", 500));
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Upstream lab gateway failed",
      );
    });
  });

  it("network failure resets the button", async () => {
    login.mockRejectedValue(
      new ApiError("Network error — check your connection", 0, {
        code: "NETWORK_ERROR",
      }),
    );
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(screen.getByRole("alert")).toHaveTextContent(/Network error/);
    });
  });

  it("timeout resets the button", async () => {
    login.mockRejectedValue(
      new ApiError("Request timed out", 408, { code: "TIMEOUT" }),
    );
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(screen.getByRole("alert")).toHaveTextContent(/timed out/i);
    });
  });
});
