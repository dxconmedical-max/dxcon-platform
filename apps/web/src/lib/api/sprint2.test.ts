import { describe, expect, it } from "vitest";

import { fetchLocations } from "./booking";
import { fetchHealthSummary } from "./patient-portal";
import { checkInPatient } from "./reception";
import { fetchQcStatus, fetchReceivedSamples, fetchVerificationQueue } from "./lab";
import {
  SAMPLE_CATALOG,
  SAMPLE_DOCTOR_REPORT,
  SAMPLE_LAB_SAMPLES,
  sampleSlots,
} from "./samples";

const ctx = { token: "t", organizationId: "o" };

describe("sample-only adapters", () => {
  it("locations resolve to labeled sample data", async () => {
    const result = await fetchLocations(ctx);
    expect(result.source).toBe("sample");
    expect(result.value.length).toBeGreaterThan(0);
    expect(result.value[0]).toHaveProperty("id");
  });

  it("health summary is AI-labeled sample data", async () => {
    const result = await fetchHealthSummary(ctx);
    expect(result.source).toBe("sample");
    expect(result.value.recommendation.toLowerCase()).toContain("review");
  });

  it("check-in echoes a checked-in status", async () => {
    const result = await checkInPatient(ctx, "Q-01");
    expect(result.value.status).toBe("CHECKED_IN");
  });

  it("lab QC / received / verification return sample lists", async () => {
    expect((await fetchQcStatus(ctx)).value.length).toBeGreaterThan(0);
    expect((await fetchReceivedSamples(ctx)).value.length).toBeGreaterThan(0);
    expect((await fetchVerificationQueue(ctx)).value.length).toBeGreaterThan(0);
  });
});

describe("sample datasets", () => {
  it("catalog items have codes and names", () => {
    expect(SAMPLE_CATALOG.length).toBeGreaterThan(0);
    for (const item of SAMPLE_CATALOG) {
      expect(item.code).toBeTruthy();
      expect(item.name).toBeTruthy();
    }
  });

  it("slot generator produces slots for a date", () => {
    const slots = sampleSlots("2026-07-14");
    expect(slots.length).toBeGreaterThan(0);
    expect(slots[0].date).toBe("2026-07-14");
  });

  it("doctor report flags abnormal analytes", () => {
    const abnormal = SAMPLE_DOCTOR_REPORT.analytes.filter((a) => a.abnormal);
    expect(abnormal.length).toBeGreaterThan(0);
  });

  it("received lab samples include an accession status", () => {
    expect(SAMPLE_LAB_SAMPLES.some((s) => s.status === "RECEIVED")).toBe(true);
  });
});
