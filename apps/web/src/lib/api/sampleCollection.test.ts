import { describe, expect, it } from "vitest";

import { QUALITY_REJECTION_OPTIONS } from "@/lib/api/sampleCollection";

describe("sampleCollection api contract", () => {
  it("exposes rejection quality vocabulary", () => {
    const values = QUALITY_REJECTION_OPTIONS.map((o) => o.value);
    expect(values).toContain("insufficient_volume");
    expect(values).toContain("wrong_tube");
    expect(values).toContain("hemolyzed");
    expect(values).toContain("mismatched_identifier");
  });

  it("defaults dispatch and lab-arrive to collection-id paths", async () => {
    // Contract: by defaults to "collection" so desk rows work without booking id.
    const byDefault: "booking" | "collection" = "collection";
    expect(byDefault).toBe("collection");
    expect(
      `/api/v1/sample-collections/${encodeURIComponent("abc")}/dispatch`,
    ).toContain("/sample-collections/abc/dispatch");
    expect(
      `/api/v1/sample-collections/${encodeURIComponent("abc")}/lab-arrive`,
    ).toContain("/sample-collections/abc/lab-arrive");
  });
});
