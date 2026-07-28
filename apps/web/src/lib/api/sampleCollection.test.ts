import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  QUALITY_REJECTION_OPTIONS,
  fetchCollectionQueue,
  type SampleCollectionAuth,
} from "@/lib/api/sampleCollection";
import { ApiError, extractApiErrorMessage, normalizeApiError } from "@/lib/errors";

describe("sampleCollection api contract", () => {
  it("exposes rejection quality vocabulary", () => {
    const values = QUALITY_REJECTION_OPTIONS.map((o) => o.value);
    expect(values).toContain("insufficient_volume");
    expect(values).toContain("wrong_tube");
    expect(values).toContain("hemolyzed");
    expect(values).toContain("mismatched_identifier");
  });
});

describe("fetchCollectionQueue include_desk + empty/records", () => {
  const originalFetch = globalThis.fetch;
  const auth: SampleCollectionAuth = {
    token: "test-token",
    organizationId: "00000000-0000-4000-8000-000000000001",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("sends include_desk=false and normalizes empty queue", async () => {
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: { items: [], count: 0, field_count: 0, desk_count: 0 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const queue = await fetchCollectionQueue(auth, { include_desk: false });
    expect(queue.items).toEqual([]);
    expect(queue.count).toBe(0);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/sample-collections/queue?include_desk=false");
    expect((init.headers as Record<string, string>)["X-Organization-ID"]).toBe(
      auth.organizationId,
    );
  });

  it("omits include_desk query when parameter is omitted and returns records", async () => {
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            items: [{ id: "c1", status: "PENDING", source: "field" }],
            count: 1,
            field_count: 1,
            desk_count: 0,
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const queue = await fetchCollectionQueue(auth, {});
    expect(queue.items).toHaveLength(1);
    expect(queue.items[0]?.id).toBe("c1");

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/sample-collections/queue");
    expect(url).not.toContain("include_desk=");
  });

  it("does not append include_desk=true (server default)", async () => {
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            items: [
              { id: "c1", status: "PENDING", source: "field" },
              { id: "d1", status: "assigned", source: "desk" },
            ],
            count: 2,
            field_count: 1,
            desk_count: 1,
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const queue = await fetchCollectionQueue(auth, { include_desk: true });
    expect(queue.desk_count).toBe(1);
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).not.toContain("include_desk=false");
  });
});

describe("collector queue error message extraction", () => {
  it("extracts backend error.message from structured 4xx envelope", () => {
    const message = extractApiErrorMessage({
      code: "FORBIDDEN",
      message: "Insufficient role permissions",
    });
    expect(message).toBe("Insufficient role permissions");
    expect(message).not.toBe("[object Object]");
  });

  it("normalizeApiError surfaces backend message for ApiError bodies", () => {
    const err = new ApiError("fallback", 403, {
      success: false,
      error: { code: "FORBIDDEN", message: "Insufficient role permissions" },
    });
    expect(normalizeApiError(err)).toBe("Insufficient role permissions");
  });

  it("normalizeApiError surfaces schema migration hint for 503", () => {
    const err = new ApiError("fallback", 503, {
      success: false,
      error: {
        code: "SERVICE_UNAVAILABLE",
        message:
          "Sample collection schema is out of date; apply backend/migrations/020_sample_collections_production.sql and backend/migrations/021_sample_collections_booking_link.sql",
      },
    });
    const text = normalizeApiError(err);
    expect(text).toContain("021_sample_collections_booking_link.sql");
    expect(text).not.toBe("[object Object]");
  });
});
