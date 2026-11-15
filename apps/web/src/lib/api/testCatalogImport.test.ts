import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/services/api", () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from "@/services/api";
import { importCatalog, parseCatalogCsv } from "./testCatalogImport";

describe("parseCatalogCsv", () => {
  it("parses quoted fields, BOM and CRLF", () => {
    const text = '﻿code,name,category,sample_type,price\r\nT-1,"Glucose, fasting",Chemistry,Serum,"80,000"\r\nT-2,"Say ""hi""",,Blood,150000\r\n';
    const { rows, error } = parseCatalogCsv(text);
    expect(error).toBeUndefined();
    expect(rows).toEqual([
      { code: "T-1", name: "Glucose, fasting", category: "Chemistry", sample_type: "Serum", price: "80000" },
      { code: "T-2", name: 'Say "hi"', category: "", sample_type: "Blood", price: "150000" },
    ]);
  });

  it("accepts semicolons and different column order", () => {
    const { rows } = parseCatalogCsv("price;code;name;category;sample_type\n100;A;Alpha;X;Blood\n");
    expect(rows[0]).toEqual({ code: "A", name: "Alpha", category: "X", sample_type: "Blood", price: "100" });
  });

  it("reports missing columns and empty files", () => {
    expect(parseCatalogCsv("code,name\nA,B\n").error).toMatch(/Thiếu cột/);
    expect(parseCatalogCsv("").error).toBeTruthy();
  });
});

describe("importCatalog", () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset());

  it("posts rows with the apply and remove_demo flags", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ success: true, data: { create: 1, update: 0, unchanged: 0, applied: false } });
    await importCatalog({ token: "t" }, [{ code: "A", name: "B", category: "", sample_type: "", price: 1 }], {
      apply: true,
      removeDemo: true,
    });
    expect(apiRequest).toHaveBeenCalledWith(
      "/api/v1/admin/test-catalog/import",
      expect.objectContaining({ method: "POST", body: expect.objectContaining({ apply: true, remove_demo: true }) }),
    );
  });
});
