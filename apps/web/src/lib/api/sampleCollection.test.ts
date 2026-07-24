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
});
