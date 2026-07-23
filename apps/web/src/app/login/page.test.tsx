import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

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

  it("shows Sign in on initial render even when auth status is loading", () => {
    render(<LoginPage />);
    const button = submitButton();
    expect(button).toHaveTextContent("Sign in");
    expect(button).toBeDisabled();
  });

  it("enables Sign in once email and password are filled", () => {
    render(<LoginPage />);
    fillCredentials();
    expect(submitButton()).toBeEnabled();
  });

  it("calls login() on submit (does not block on auth bootstrap loading)", async () => {
    login.mockResolvedValue({ redirect: "/app" });
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("user@example.com", "secret", false);
    });
  });

  it("clears Signing in... after login rejects", async () => {
    login.mockRejectedValue(new Error("fail"));
    render(<LoginPage />);
    fillCredentials();
    fireEvent.submit(submitButton().closest("form")!);
    await waitFor(() => {
      expect(submitButton()).toHaveTextContent("Sign in");
      expect(submitButton()).toBeEnabled();
    });
  });
});
