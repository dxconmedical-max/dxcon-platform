import { describe, expect, it } from "vitest";

import { buildNavItems } from "@/lib/navigation";
import type { AuthCapabilities } from "@/services/auth";

describe("buildNavItems", () => {
  it("always includes overview", () => {
    const items = buildNavItems(null);
    expect(items.some((i) => i.href === "/app")).toBe(true);
  });

  it("filters by workspace for non-admin", () => {
    const capabilities: AuthCapabilities = {
      user: { id: "1", email: "d@x.com", role: "DOCTOR" },
      organization: null,
      membership: {
        membership_id: "m",
        organization_id: "o",
        role_code: "DOCTOR",
        membership_status: "active",
      },
      workspace: "/app/doctor",
      default_workspace: "/app/doctor",
      permissions: ["portal.doctor.read"],
      features: [],
    };
    const items = buildNavItems(capabilities);
    expect(items.some((i) => i.href === "/app/doctor")).toBe(true);
  });
});
