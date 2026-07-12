import { describe, expect, it } from "vitest";

import { ApiError, loginErrorMessage, normalizeApiError } from "@/lib/errors";

function err(status: number, message = "x", code?: string) {
  return new ApiError({ code: code ?? "ERR", message, status, retryable: false });
}

describe("normalizeApiError", () => {
  it("returns ApiError message", () => {
    expect(normalizeApiError(err(429, "Too many requests"))).toBe("Too many requests");
  });

  it("maps network errors", () => {
    expect(normalizeApiError(err(0, "Network error"))).toContain("Network");
  });
});

describe("loginErrorMessage", () => {
  it("maps invalid credentials", () => {
    expect(loginErrorMessage(err(401))).toContain("Invalid email");
  });

  it("maps disabled account", () => {
    expect(loginErrorMessage(err(403))).toContain("disabled");
  });

  it("maps rate limit", () => {
    expect(loginErrorMessage(err(429))).toContain("Too many");
  });
});
