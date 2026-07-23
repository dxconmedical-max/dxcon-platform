import { describe, expect, it } from "vitest";

import { ApiError, normalizeApiError } from "@/lib/errors";

describe("normalizeApiError", () => {
  it("maps 429 to rate limit message", () => {
    expect(normalizeApiError(new ApiError("x", 429))).toContain("Too many attempts");
  });

  it("maps network errors", () => {
    expect(normalizeApiError(new ApiError("x", 0))).toContain("Network error");
  });

  it("extracts API error body", () => {
    expect(
      normalizeApiError(new ApiError("x", 401, { error: "Invalid credentials" })),
    ).toBe("Invalid credentials");
  });

  it("does not label 4xx as network error", () => {
    expect(normalizeApiError(new ApiError("nope", 404))).toBe("nope");
  });
});