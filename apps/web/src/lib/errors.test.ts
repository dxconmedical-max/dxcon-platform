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

  it("only uses network copy for transport failures", () => {
    expect(loginErrorMessage(err(0))).toContain("Network error");
    expect(loginErrorMessage(err(408))).toContain("Network error");
    expect(loginErrorMessage(err(500, "boom"))).toBe("boom");
  });
});

describe("mapResponseToApiError envelope", () => {
  it("reads nested data.error when top-level error is null", async () => {
    const { mapResponseToApiError } = await import("@/lib/errors");
    const err = mapResponseToApiError(401, {
      success: true,
      data: { error: "Invalid credentials" },
      error: null,
    });
    expect(err.status).toBe(401);
    expect(err.message).toBe("Invalid credentials");
  });
});
