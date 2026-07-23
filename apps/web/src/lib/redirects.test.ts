import { describe, expect, it } from "vitest";

import {
  publicSiteAppRedirectTarget,
  sameNormalizedUrl,
  wwwToApexTarget,
} from "@/lib/redirects";

describe("sameNormalizedUrl", () => {
  it("matches protocol, host, port, path, and search", () => {
    expect(
      sameNormalizedUrl(
        "https://dxcon.com.vn/login?next=%2Fapp",
        "https://dxcon.com.vn/login?next=%2Fapp",
      ),
    ).toBe(true);
    expect(
      sameNormalizedUrl(
        "https://dxcon.com.vn/login/",
        "https://dxcon.com.vn/login",
      ),
    ).toBe(true);
    expect(
      sameNormalizedUrl("https://dxcon.com.vn/login", "https://www.dxcon.com.vn/login"),
    ).toBe(false);
    expect(
      sameNormalizedUrl("https://dxcon.com.vn/login", "https://dxcon.com.vn/login?x=1"),
    ).toBe(false);
  });
});

describe("wwwToApexTarget", () => {
  it("redirects www once to apex preserving path and query", () => {
    const target = wwwToApexTarget("https://www.dxcon.com.vn/login?next=%2Fapp");
    expect(target).not.toBeNull();
    expect(target!.toString()).toBe("https://dxcon.com.vn/login?next=%2Fapp");
  });

  it("does not redirect apex to www", () => {
    expect(wwwToApexTarget("https://dxcon.com.vn/login")).toBeNull();
  });
});

describe("publicSiteAppRedirectTarget", () => {
  it("does not redirect dxcon.com.vn/login to itself when APP_URL is apex", () => {
    const target = publicSiteAppRedirectTarget(
      "https://dxcon.com.vn/login",
      "/login",
      "",
      "https://dxcon.com.vn",
    );
    expect(target).toBeNull();
  });

  it("does not redirect dxcon.com.vn/app/admin to itself when APP_URL is apex", () => {
    const target = publicSiteAppRedirectTarget(
      "https://dxcon.com.vn/app/admin",
      "/app/admin",
      "",
      "https://dxcon.com.vn",
    );
    expect(target).toBeNull();
  });

  it("preserves query when bouncing to a different APP_URL origin", () => {
    const target = publicSiteAppRedirectTarget(
      "https://dxcon.com.vn/login?next=%2Fapp%2Fadmin",
      "/login",
      "?next=%2Fapp%2Fadmin",
      "https://app.dxcon.com.vn",
    );
    expect(target).not.toBeNull();
    expect(target!.toString()).toBe(
      "https://app.dxcon.com.vn/login?next=%2Fapp%2Fadmin",
    );
  });

  it("does not redirect when APP_URL shares the same origin", () => {
    const target = publicSiteAppRedirectTarget(
      "https://dxcon.com.vn/login",
      "/login",
      "",
      "https://dxcon.com.vn/",
    );
    expect(target).toBeNull();
  });

  it("does not redirect when only protocol differs (proxy http vs https APP_URL)", () => {
    const target = publicSiteAppRedirectTarget(
      "http://dxcon.com.vn/login",
      "/login",
      "",
      "https://dxcon.com.vn",
    );
    expect(target).toBeNull();
  });

  it("does not redirect to www when APP_URL is www (canonicalizes then same-host)", () => {
    const target = publicSiteAppRedirectTarget(
      "https://dxcon.com.vn/login",
      "/login",
      "",
      "https://www.dxcon.com.vn",
    );
    expect(target).toBeNull();
  });

  it("uses Host header when request URL is loopback (local prod verify)", () => {
    const target = publicSiteAppRedirectTarget(
      "http://127.0.0.1:3000/login",
      "/login",
      "",
      "https://dxcon.com.vn",
      "dxcon.com.vn",
    );
    expect(target).toBeNull();
  });
});
