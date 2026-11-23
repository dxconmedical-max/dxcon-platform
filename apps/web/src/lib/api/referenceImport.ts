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

export type ActivateResult = { activated: number; superseded: number; counts: Record<string, number> };

export async function activateReferenceRanges(ctx: Ctx, confirm: string): Promise<ActivateResult> {
  const res = await apiRequest<ActivateResult & { data?: ActivateResult }>(
    "/api/v1/reference-ranges-import/activate",
    { method: "POST", body: { confirm }, token: ctx.token, organizationId: ctx.organizationId },
  );
  return (res.data ?? res) as ActivateResult;
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Không đọc được file."));
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.readAsDataURL(file);
  });
}

export async function fetchReferenceCounts(ctx: Ctx): Promise<Record<string, number>> {
  const res = await apiRequest<{ counts: Record<string, number>; data?: { counts: Record<string, number> } }>(
    "/api/v1/reference-ranges-import",
    { token: ctx.token, organizationId: ctx.organizationId },
  );
  return (res.data?.counts ?? res.counts) as Record<string, number>;
}
