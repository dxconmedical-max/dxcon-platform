import { apiRequest } from "@/services/api";

type Ctx = { token: string | null; organizationId: string | null };

export type ImportReport = {
  rows_in_file: number;
  importable: number;
  text_only_skipped: number;
  no_range_skipped: number;
  conflict_skipped?: number;
  warnings: string[];
  warnings_total: number;
  applied: boolean;
  counts: Record<string, number>;
};

export async function importReferenceFile(ctx: Ctx, fileB64: string, apply: boolean): Promise<ImportReport> {
  const res = await apiRequest<{ report: ImportReport; data?: { report: ImportReport } }>(
    "/api/v1/reference-ranges-import",
    { method: "POST", body: { file_b64: fileB64, apply }, token: ctx.token, organizationId: ctx.organizationId },
  );
  return (res.data?.report ?? res.report) as ImportReport;
}

export async function activateReferenceRanges(ctx: Ctx, confirm: string) {
  const res = await apiRequest<{ activated: number; superseded: number; data?: { activated: number; superseded: number } }>(
    "/api/v1/reference-ranges-import/activate",
    { method: "POST", body: { confirm }, token: ctx.token, organizationId: ctx.organizationId },
  );
  return res.data ?? res;
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Không đọc được file."));
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.readAsDataURL(file);
  });
}
