import { describe, expect, it } from "vitest";

import { can, canAny, hasFeature } from "@/lib/permissions";
import type { AuthCapabilities } from "@/services/auth";

const capabilities: AuthCapabilities = {
  user: { id: "1", email: "a@b.com", role: "DOCTOR" },
  organization: null,
  membership: {
    membership_id: "m1",
    organization_id: "o1",
    role_code: "DOCTOR",
    membership_status: "active",
  },
  workspace: "/app/doctor",
  default_workspace: "/app/doctor",
  permissions: ["portal.doctor.read", "data.view"],
  features: ["HOME_COLLECTION"],
};

describe("permission helpers", () => {
  it("can checks single permission", () => {
    expect(can(capabilities, "portal.doctor.read")).toBe(true);
    expect(can(capabilities, "users.write")).toBe(false);
  });

  it("canAny checks any permission", () => {
    expect(canAny(capabilities, ["users.write", "data.view"])).toBe(true);
  });

  it("hasFeature checks feature flags", () => {
    expect(hasFeature(capabilities, "HOME_COLLECTION")).toBe(true);
    expect(hasFeature(capabilities, "LIS_REALTIME")).toBe(false);
  });
});
