import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

vi.mock("@/lib/constants", () => ({
  APP_URL: "https://dxcon.com.vn",
  PUBLIC_SITE_URL: "https://dxcon.com.vn",
  AUTH_COOKIE: "dxcon_authenticated",
  ROLE_COOKIE: "dxcon_role",
  APP_ENV: "production",
  IS_PRODUCTION: true,
  DEMO_MODE: false,
  IS_STAGING: false,
  API_BASE_URL: "https://api.dxcon.com.vn",
}));

import { middleware } from "@/middleware";

function makeRequest(url: string, cookie?: string): NextRequest {
  const parsed = new URL(url);
  const headers = new Headers({ host: parsed.host });
  if (cookie) headers.set("cookie", cookie);
  return new NextRequest(parsed, { headers });
}

describe("middleware production routing", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("does not redirect dxcon.com.vn/login to itself", () => {
    const response = middleware(makeRequest("https://dxcon.com.vn/login"));
    expect(response.status).not.toBe(307);
    expect(response.status).not.toBe(308);
    expect(response.headers.get("location")).toBeNull();
    expect(response.status).toBe(200);
  });

  it("does not redirect dxcon.com.vn/app/admin to itself when unauthenticated — goes to login", () => {
    const response = middleware(makeRequest("https://dxcon.com.vn/app/admin"));
    expect(response.status).toBe(307);
    const location = response.headers.get("location");
    expect(location).toBeTruthy();
    expect(new URL(location!).pathname).toBe("/login");
    expect(new URL(location!).searchParams.get("next")).toBe("/app/admin");
    // Must not bounce to the same /app/admin URL
    expect(new URL(location!).pathname).not.toBe("/app/admin");
  });

  it("redirects www.dxcon.com.vn/login once to apex /login", () => {
    const response = middleware(makeRequest("https://www.dxcon.com.vn/login"));
    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe("https://dxcon.com.vn/login");
  });

  it("redirects authenticated /login to workspace", () => {
    const response = middleware(
      makeRequest(
        "https://dxcon.com.vn/login",
        "dxcon_authenticated=1; dxcon_role=admin",
      ),
    );
    expect(response.status).toBe(307);
    expect(new URL(response.headers.get("location")!).pathname).toMatch(/^\/app/);
  });

  it("redirects unauthenticated protected routes to login", () => {
    const response = middleware(makeRequest("https://dxcon.com.vn/app/lab"));
    expect(response.status).toBe(307);
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/login");
    expect(location.searchParams.get("next")).toBe("/app/lab");
  });

  it("allows authenticated workspace access without redirect loop", () => {
    const response = middleware(
      makeRequest(
        "https://dxcon.com.vn/app/admin",
        "dxcon_authenticated=1; dxcon_role=admin",
      ),
    );
    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });

  it("keeps legacy redirects working", () => {
    const response = middleware(makeRequest("https://dxcon.com.vn/admin"));
    expect(response.status).toBe(307);
    expect(new URL(response.headers.get("location")!).pathname).toBe("/app/admin");
  });

  it("preserves query string on www → apex redirect", () => {
    const response = middleware(
      makeRequest("https://www.dxcon.com.vn/login?next=%2Fapp%2Fadmin"),
    );
    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe(
      "https://dxcon.com.vn/login?next=%2Fapp%2Fadmin",
    );
  });
});
