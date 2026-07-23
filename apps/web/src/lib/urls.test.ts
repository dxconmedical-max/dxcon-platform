import { describe, expect, it, vi } from "vitest";

import { safeRedirectPath } from "@/lib/urls";

describe("urls", () => {
  it("rejects open redirects", () => {
    expect(safeRedirectPath("https://evil.test")).toBe("/app");
    expect(safeRedirectPath("//evil.test")).toBe("/app");
    expect(safeRedirectPath("/app/reception")).toBe("/app/reception");
  });

  it("returns relative login on preview hosts", async () => {
    const { loginUrl } = await import("@/lib/urls");
    expect(loginUrl("localhost:3000")).toBe("/login");
  });

  it("returns relative login when APP_URL shares the public host", async () => {
    vi.resetModules();
    vi.doMock("@/lib/constants", async () => {
      const actual = await vi.importActual<typeof import("@/lib/constants")>(
        "@/lib/constants",
      );
      return {
        ...actual,
        APP_URL: "https://dxcon.com.vn",
        APP_ENV: "production",
        IS_PRODUCTION: true,
      };
    });
    const { loginUrl } = await import("@/lib/urls");
    expect(loginUrl("dxcon.com.vn")).toBe("/login");
    vi.doUnmock("@/lib/constants");
    vi.resetModules();
  });
});
