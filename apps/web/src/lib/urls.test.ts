import { describe, expect, it } from "vitest";

import { loginUrl, safeRedirectPath } from "@/lib/urls";

describe("urls", () => {
  it("rejects open redirects", () => {
    expect(safeRedirectPath("https://evil.test")).toBe("/app");
    expect(safeRedirectPath("//evil.test")).toBe("/app");
    expect(safeRedirectPath("/app/reception")).toBe("/app/reception");
  });

  it("returns relative login on preview hosts", () => {
    expect(loginUrl("localhost:3000")).toBe("/login");
  });
});
