import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";

describe("apiRequest auth integration", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("POSTs login path with JSON body", async () => {
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ success: true, access_token: "a" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    await apiRequest("/api/v1/auth/login", {
      method: "POST",
      body: { email: "a@b.com", password: "x" },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/auth/login");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({
      email: "a@b.com",
      password: "x",
    });
  });

  it("maps abort to timeout ApiError", async () => {
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockImplementation((_url: string, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          const err = new Error("aborted");
          err.name = "AbortError";
          reject(err);
        });
      });
    });

    await expect(
      apiRequest("/api/v1/auth/login", {
        method: "POST",
        body: { email: "a@b.com", password: "x" },
        timeoutMs: 20,
      }),
    ).rejects.toMatchObject({ status: 408, name: "ApiError" } satisfies Partial<ApiError>);
  });

  it("maps HTTP 401 to ApiError without calling it a network error", async () => {
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ error: "Invalid credentials" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(
      apiRequest("/api/v1/auth/login", {
        method: "POST",
        body: { email: "a@b.com", password: "bad" },
      }),
    ).rejects.toMatchObject({ status: 401, message: "Invalid credentials" });
  });
});
