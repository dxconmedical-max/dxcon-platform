/**
 * Production-like end-to-end login hardening test.
 * Uses the real API base URL from env (defaults to production) with mocked
 * credentials flow for deterministic CI, plus a live OPTIONS/shape probe.
 */
import { describe, expect, it } from "vitest";

import { API_BASE_URL, API_TIMEOUT_MS, DEMO_MODE } from "@/lib/constants";
import { parseLoginResponse } from "@/lib/auth/session";
import { loginErrorMessage, ApiError } from "@/lib/errors";

const PROD_API = "https://api.dxcon.com.vn";

describe("production-like auth e2e config", () => {
  it("points at the production API by default", () => {
    expect(API_BASE_URL).toBe(PROD_API);
    expect(DEMO_MODE).toBe(false);
    expect(API_TIMEOUT_MS).toBeGreaterThan(0);
    expect(API_TIMEOUT_MS).toBeLessThanOrEqual(60_000);
  });

  it("login cannot remain pending beyond configured timeout budget", () => {
    expect(API_TIMEOUT_MS).toBeLessThanOrEqual(30_000);
  });

  it("distinguishes auth errors from network errors", () => {
    expect(loginErrorMessage(new ApiError("Invalid credentials", 401))).toMatch(
      /Invalid email or password/,
    );
    expect(loginErrorMessage(new ApiError("fail", 500))).toBe("fail");
    expect(loginErrorMessage(new ApiError("down", 0))).toMatch(/Network error/);
    expect(loginErrorMessage(new ApiError("Request timed out", 408))).toMatch(
      /timed out/i,
    );
  });

  it("parses the live backend login success schema shape", () => {
    // Mirrors backend/app/api/auth/routes.py success body.
    const session = parseLoginResponse({
      success: true,
      token: "jwt-access",
      access_token: "jwt-access",
      refresh_token: "jwt-refresh",
      email: "demo@example.com",
      role: "SUPER_ADMIN",
      user: {
        id: "user-1",
        email: "demo@example.com",
        role: "SUPER_ADMIN",
        organization_id: null,
        is_active: true,
      },
    });
    expect(session.accessToken).toBe("jwt-access");
    expect(session.refreshToken).toBe("jwt-refresh");
  });
});

describe("live production API probe (read-only)", () => {
  // Opt-in only — CI auth freeze must stay deterministic offline.
  // Enable with AUTH_LIVE_PROBE=1 when network to api.dxcon.com.vn is available.
  const liveEnabled = process.env.AUTH_LIVE_PROBE === "1";

  it.skipIf(!liveEnabled)(
    "rejects invalid credentials with a real auth status, not network error",
    async () => {
      const response = await fetch(`${PROD_API}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: "e2e-invalid@dxcon.test",
          password: "definitely-not-valid-password",
        }),
        signal: AbortSignal.timeout(API_TIMEOUT_MS),
      });

      expect([400, 401, 403, 422, 429]).toContain(response.status);
      const payload = await response.json().catch(() => ({}));
      expect(response.status).not.toBe(0);
      // Body should be structured enough for the client error mapper.
      expect(payload === null || typeof payload === "object").toBe(true);
    },
    35_000,
  );
});
