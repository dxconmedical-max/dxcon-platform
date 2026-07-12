import { describe, expect, it } from "vitest";

import { hostKind, isAppHost, isPublicSiteHost, isPreviewHost } from "@/lib/domains";

describe("domains", () => {
  it("classifies production marketing hosts", () => {
    expect(isPublicSiteHost("dxcon.com.vn")).toBe(true);
    expect(isPublicSiteHost("www.dxcon.com.vn")).toBe(true);
    expect(hostKind("dxcon.com.vn")).toBe("public_site");
  });

  it("classifies application host", () => {
    expect(isAppHost("app.dxcon.com.vn")).toBe(true);
    expect(hostKind("app.dxcon.com.vn")).toBe("application");
  });

  it("treats unknown hosts as preview", () => {
    expect(isPreviewHost("dxcon-web.vercel.app")).toBe(true);
    expect(hostKind("localhost:3000")).toBe("preview");
  });
});
