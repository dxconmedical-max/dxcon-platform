import { describe, expect, it } from "vitest";

import { withSampleFallback } from "./adapter";
import { ApiError } from "@/lib/errors";

describe("withSampleFallback", () => {
  it("returns live data when the loader succeeds", async () => {
    const result = await withSampleFallback(async () => ["live"], ["sample"]);
    expect(result.source).toBe("live");
    expect(result.value).toEqual(["live"]);
  });

  it("falls back to sample data on a generic error", async () => {
    const result = await withSampleFallback(
      async () => {
        throw new Error("boom");
      },
      ["sample"],
      "note",
    );
    expect(result.source).toBe("sample");
    expect(result.value).toEqual(["sample"]);
    expect(result.note).toBe("note");
  });

  it("falls back to sample data on a 500 ApiError", async () => {
    const result = await withSampleFallback(
      async () => {
        throw new ApiError({ code: "SERVER", message: "x", status: 500, retryable: true });
      },
      "sample",
    );
    expect(result.source).toBe("sample");
    expect(result.value).toBe("sample");
  });

  it("re-throws on 401 so the shell can redirect to login", async () => {
    await expect(
      withSampleFallback(async () => {
        throw new ApiError({ code: "UNAUTHORIZED", message: "x", status: 401, retryable: false });
      }, "sample"),
    ).rejects.toBeInstanceOf(ApiError);
  });

  it("re-throws on 403 so the shell can redirect to forbidden", async () => {
    await expect(
      withSampleFallback(async () => {
        throw new ApiError({ code: "FORBIDDEN", message: "x", status: 403, retryable: false });
      }, "sample"),
    ).rejects.toBeInstanceOf(ApiError);
  });
});
