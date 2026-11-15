import { apiRequest } from "@/services/api";

export type CatalogRow = {
  code: string;
  name: string;
  category: string;
  sample_type: string;
  price: number | string;
};

export type ImportSummary = {
  create: number;
  update: number;
  unchanged: number;
  demo_present: number;
  demo_to_remove: number;
  applied: boolean;
  preview?: { create: CatalogRow[]; update: CatalogRow[] };
};

const COLUMNS = ["code", "name", "category", "sample_type", "price"] as const;

/** Split CSV text into records. Handles quotes, escaped quotes, CRLF and a UTF-8 BOM. */
function splitRecords(text: string, delimiter: string): string[][] {
  const records: string[][] = [];
  let field = "";
  let record: string[] = [];
  let quoted = false;
  const input = text.replace(/^﻿/, "");
  for (let i = 0; i < input.length; i += 1) {
    const ch = input[i];
    if (quoted) {
      if (ch === '"' && input[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === delimiter) {
      record.push(field);
      field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && input[i + 1] === "\n") i += 1;
      record.push(field);
      field = "";
      if (record.some((value) => value.trim() !== "")) records.push(record);
      record = [];
    } else {
      field += ch;
    }
  }
  record.push(field);
  if (record.some((value) => value.trim() !== "")) records.push(record);
  return records;
}

/** Parse the catalog CSV (columns: code, name, category, sample_type, price). */
export function parseCatalogCsv(text: string): { rows: CatalogRow[]; error?: string } {
  const firstLine = text.replace(/^﻿/, "").split(/\r?\n/, 1)[0] ?? "";
  const delimiter = firstLine.split(";").length > firstLine.split(",").length ? ";" : ",";
  const records = splitRecords(text, delimiter);
  if (records.length < 2) return { rows: [], error: "File trống hoặc thiếu dòng dữ liệu." };
  const header = records[0].map((h) => h.trim().toLowerCase());
  const index = COLUMNS.map((name) => header.indexOf(name));
  const missing = COLUMNS.filter((_, i) => index[i] < 0);
  if (missing.length > 0) {
    return { rows: [], error: `Thiếu cột: ${missing.join(", ")}. Dòng đầu phải là: ${COLUMNS.join(",")}` };
  }
  const rows = records.slice(1).map((record) => {
    const get = (i: number) => (record[index[i]] ?? "").trim();
    return {
      code: get(0),
      name: get(1),
      category: get(2),
      sample_type: get(3),
      price: get(4).replace(/[.,\s]/g, ""),
    };
  });
  return { rows };
}

type Ctx = { token: string; organizationId?: string | null };

export async function importCatalog(
  ctx: Ctx,
  rows: CatalogRow[],
  options: { apply: boolean; removeDemo: boolean },
): Promise<ImportSummary> {
  const response = await apiRequest<{ success: boolean; data: ImportSummary }>(
    "/api/v1/admin/test-catalog/import",
    {
      method: "POST",
      token: ctx.token,
      organizationId: ctx.organizationId ?? null,
      body: { rows, apply: options.apply, remove_demo: options.removeDemo },
      timeoutMs: 60_000,
    },
  );
  return response.data;
}
