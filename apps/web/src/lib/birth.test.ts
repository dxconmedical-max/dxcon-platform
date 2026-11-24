import { describe, expect, it } from "vitest";

import { formatBirth, parseBirthInput } from "./birth";

const NOW = new Date(2026, 10, 24);

describe("parseBirthInput", () => {
  it("keeps a bare year as year only", () => {
    expect(parseBirthInput("1985", NOW).value).toEqual({ year: 1985, date: null });
  });
  it("parses dd/mm/yyyy", () => {
    expect(parseBirthInput("7/3/1985", NOW).value).toEqual({ year: 1985, date: "1985-03-07" });
  });
  it("rejects impossible or future dates", () => {
    expect(parseBirthInput("31/02/1990", NOW).error).toBeTruthy();
    expect(parseBirthInput("01/01/2999", NOW).error).toBeTruthy();
    expect(parseBirthInput("abc", NOW).error).toBeTruthy();
    expect(parseBirthInput("1800", NOW).error).toBeTruthy();
  });
});

describe("formatBirth", () => {
  it("shows the full date when known and only the year otherwise", () => {
    expect(formatBirth("1985-03-07", 1985)).toBe("07/03/1985");
    expect(formatBirth(null, 1985)).toBe("1985");
    expect(formatBirth("1985")).toBe("1985");
    expect(formatBirth(null)).toBe("—");
  });
});
