import { describe, expect, it } from "vitest";

import type { RoleDashboardKey } from "@/lib/api/roleDashboards";

describe("roleDashboards api contract", () => {
  it("exposes expected role keys", () => {
    const roles: RoleDashboardKey[] = [
      "admin",
      "administration",
      "reception",
      "laboratory",
      "lab",
      "collector",
      "doctor",
      "patient",
    ];
    expect(roles).toContain("laboratory");
    expect(roles).toContain("reception");
    expect(roles).toHaveLength(8);
  });
});
