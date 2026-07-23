import { beforeEach, describe, expect, it, vi } from "vitest";

import { parseLoginResponse } from "@/lib/auth/session";
import { ApiError } from "@/lib/errors";
import { migratePersistedAuth } from "@/stores/authStore";

describe("parseLoginResponse", () => {
  it("accepts flat production login payload", () => {
    const session = parseLoginResponse({
      success: true,
      token: "access-1",
      access_token: "access-1",
      refresh_token: "refresh-1",
      email: "a@b.com",
      role: "ADMIN",
      user: { id: "u1", email: "a@b.com", role: "ADMIN" },
    });
    expect(session.accessToken).toBe("access-1");
    expect(session.refreshToken).toBe("refresh-1");
    expect(session.role).toBe("ADMIN");
  });

  it("accepts enveloped data payloads", () => {
    const session = parseLoginResponse({
      success: true,
      data: {
        access_token: "a",
        refresh_token: "r",
        user: { id: "1", email: "x@y.com", role: "DOCTOR" },
      },
    });
    expect(session.user.role).toBe("DOCTOR");
  });

  it("rejects malformed payloads", () => {
    expect(() => parseLoginResponse({ success: true })).toThrow(ApiError);
    expect(() => parseLoginResponse(null)).toThrow(ApiError);
  });
});

describe("migratePersistedAuth", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("strips legacy isLoading=true and isSubmittingLogin=true", () => {
    const cleaned = migratePersistedAuth({
      accessToken: "tok",
      refreshToken: "ref",
      user: { id: "1", email: "a@b.com", role: "ADMIN" },
      role: "ADMIN",
      status: "loading",
      isLoading: true,
      isSubmittingLogin: true,
      isInitializingSession: true,
      isRefreshingSession: true,
      error: "stale",
      isHydrated: false,
    });
    expect(cleaned.isLoading).toBeUndefined();
    expect(cleaned.isSubmittingLogin).toBeUndefined();
    expect(cleaned.isInitializingSession).toBeUndefined();
    expect(cleaned.status).toBeUndefined();
    expect(cleaned.error).toBeUndefined();
    expect(cleaned.accessToken).toBe("tok");
  });

  it("discards incompatible snapshots without a valid user", () => {
    expect(
      migratePersistedAuth({
        accessToken: "tok",
        isLoading: true,
        user: { email: "bad" },
      }),
    ).toEqual({});
  });
});
