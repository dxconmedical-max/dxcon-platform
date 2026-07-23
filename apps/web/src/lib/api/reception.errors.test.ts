import { describe, expect, it } from "vitest";

import { ApiError, isRequestAborted, normalizeApiError } from "@/lib/errors";

describe("normalizeApiError reception safety", () => {
  it("does not call HTTP 403 a network error", () => {
    expect(normalizeApiError(new ApiError("Forbidden", 403, { error: "Forbidden" }))).toBe(
      "Forbidden",
    );
    expect(normalizeApiError(new ApiError("x", 403))).not.toMatch(/Network error/i);
  });

  it("does not call HTTP 500 a network error", () => {
    expect(normalizeApiError(new ApiError("Server boom", 500))).toBe("Server boom");
  });

  it("maps aborted requests distinctly", () => {
    const err = new ApiError("Request cancelled", 499, { code: "ABORTED" });
    expect(isRequestAborted(err)).toBe(true);
    expect(normalizeApiError(err)).toContain("cancelled");
  });

  it("maps timeout without calling it a network error", () => {
    expect(normalizeApiError(new ApiError("Request timed out", 408, { code: "TIMEOUT" }))).toMatch(
      /timed out/i,
    );
  });
});
