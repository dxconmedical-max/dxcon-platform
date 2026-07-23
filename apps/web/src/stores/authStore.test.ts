import { describe, expect, it } from "vitest";

import { sanitizePersistedAuth } from "@/stores/authStore";

describe("sanitizePersistedAuth", () => {
  it("strips stale loading / status flags from persisted payload", () => {
    const cleaned = sanitizePersistedAuth({
      accessToken: "tok",
      refreshToken: "ref",
      status: "loading",
      isLoading: true,
      isHydrated: false,
      error: "stale",
      isSubmittingLogin: true,
      user: { id: "1", email: "a@b.com", role: "ADMIN" },
    });

    expect(cleaned.status).toBeUndefined();
    expect(cleaned.isLoading).toBeUndefined();
    expect(cleaned.isHydrated).toBeUndefined();
    expect(cleaned.error).toBeUndefined();
    expect(cleaned.isSubmittingLogin).toBeUndefined();
    expect(cleaned.accessToken).toBe("tok");
    expect(cleaned.refreshToken).toBe("ref");
  });

  it("returns empty object for invalid input", () => {
    expect(sanitizePersistedAuth(null)).toEqual({});
    expect(sanitizePersistedAuth("x")).toEqual({});
  });
});
