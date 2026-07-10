import { describe, expect, it } from "vitest";

import {
  DEFAULT_WORKSPACE,
  ROLE_WORKSPACE_ROUTES,
  workspacePathForRole,
} from "@/lib/roles";

describe("workspacePathForRole", () => {
  it("routes doctor roles to doctor workspace", () => {
    expect(workspacePathForRole("DOCTOR")).toBe("/app/doctor");
    expect(workspacePathForRole("PARTNER_DOCTOR")).toBe("/app/doctor");
  });

  it("routes admin roles to admin workspace", () => {
    expect(workspacePathForRole("SUPER_ADMIN")).toBe("/app/admin");
    expect(workspacePathForRole("SYSTEM_ADMIN")).toBe("/app/admin");
  });

  it("falls back to default workspace", () => {
    expect(workspacePathForRole("UNKNOWN")).toBe(DEFAULT_WORKSPACE);
  });

  it("covers epic compatibility roles", () => {
    expect(ROLE_WORKSPACE_ROUTES.PARTNER_COLLECTOR).toBe("/app/collector");
    expect(ROLE_WORKSPACE_ROUTES.PARTNER_LAB_MANAGER).toBe("/app/lab");
    expect(ROLE_WORKSPACE_ROUTES.PARTNER_CLINIC_OWNER).toBe("/app/clinic");
  });
});
