import { describe, expect, it } from "vitest";

import { WORKSPACE_DEFINITIONS, workspaceByKey, workspaceByPath } from "@/lib/workspaces";

describe("workspaces", () => {
  it("defines all role workspaces", () => {
    const paths = Object.values(WORKSPACE_DEFINITIONS).map((ws) => ws.path);
    expect(paths).toContain("/app/admin");
    expect(paths).toContain("/app/reception");
    expect(paths).toContain("/app/patient");
  });

  it("resolves workspace by path", () => {
    expect(workspaceByPath("/app/lab")?.key).toBe("lab");
  });

  it("uses verified API dashboard paths", () => {
    expect(workspaceByKey("reception").dashboardPath).toBe(
      "/api/v1/reception/workspace/dashboard",
    );
    expect(workspaceByKey("lab").dashboardPath).toBe("/api/v1/lab/workspace/dashboard");
    expect(workspaceByKey("doctor").dashboardPath).toBe("/api/v1/portal/doctor/dashboard");
  });

  it("returns placeholder cards when data is empty", () => {
    const cards = workspaceByKey("reception").extractStatusCards({});
    expect(cards).toHaveLength(4);
    expect(cards.every((c) => c.value === "—")).toBe(true);
  });
});
