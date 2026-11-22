"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { activateReferenceRanges, fileToBase64, importReferenceFile, type ImportReport } from "@/lib/api/referenceImport";
import { normalizeApiError } from "@/lib/errors";

export default function ReferenceRangesImportPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = { token: accessToken, organizationId: activeOrganizationId };
  const [b64, setB64] = useState("");
  const [fileName, setFileName] = useState("");
  const [report, setReport] = useState<ImportReport | null>(null);
  const [phrase, setPhrase] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(apply: boolean) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      setReport(await importReferenceFile(ctx, b64, apply));
      if (apply) setNotice("Đã nạp ở trạng thái NHÁP. Chưa dùng để đánh cờ kết quả.");
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function activate() {
    setBusy(true);
    setError(null);
    try {
      const r = await activateReferenceRanges(ctx, phrase);
      setNotice(`Đã kích hoạt ${r.activated} dòng (thay thế ${r.superseded} dòng cũ).`);
      setPhrase("");
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Khoảng tham chiếu" workspacePath="/app/admin">
      <div className="max-w-3xl space-y-5 text-sm">
        <p className="text-slate-600">
          Tải file Excel khoảng tham chiếu. Bước 1 chỉ xem trước. Bước 2 nạp ở trạng thái nháp. Bước 3 chỉ kích hoạt sau
          khi trưởng khoa xét nghiệm đã duyệt, vì khi kích hoạt hệ thống sẽ dùng các khoảng này để đánh cờ cao/thấp.
        </p>
        <Input
          type="file"
          accept=".xlsx"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            setReport(null);
            if (!f) return;
            setFileName(f.name);
            setB64(await fileToBase64(f));
          }}
        />
        <div className="flex gap-2">
          <Button variant="outline" disabled={!b64 || busy} onClick={() => void run(false)}>
            1. Xem trước {fileName ? `(${fileName})` : ""}
          </Button>
          <Button disabled={!b64 || busy || !report} onClick={() => void run(true)}>
            2. Nạp bản nháp
          </Button>
        </div>
        {error ? <p className="text-red-600">{error}</p> : null}
        {notice ? <p className="text-emerald-700">{notice}</p> : null}
        {report ? (
          <div className="rounded-lg border border-slate-200 p-4">
            <p>Số dòng trong file: {report.rows_in_file}</p>
            <p>Nạp được (có khoảng số): {report.importable}</p>
            <p>Bỏ qua vì chỉ có chữ (định tính): {report.text_only_skipped}</p>
            <p>Bỏ qua vì không có khoảng: {report.no_range_skipped}</p>
            <p>Hiện có trong hệ thống: {Object.entries(report.counts).map(([k, v]) => `${k} ${v}`).join(", ") || "chưa có"}</p>
            {report.warnings_total > 0 ? (
              <details className="mt-2">
                <summary className="cursor-pointer text-amber-700">{report.warnings_total} dòng cần kiểm tra lại</summary>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">
                  {report.warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              </details>
            ) : null}
          </div>
        ) : null}
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
          <p className="font-medium">3. Kích hoạt (chỉ SUPER_ADMIN)</p>
          <p className="mt-1 text-xs text-slate-600">Gõ đúng cụm: TOI XAC NHAN</p>
          <div className="mt-2 flex gap-2">
            <Input value={phrase} onChange={(e) => setPhrase(e.target.value)} placeholder="TOI XAC NHAN" />
            <Button variant="secondary" disabled={busy || phrase.trim().toUpperCase() !== "TOI XAC NHAN"} onClick={() => void activate()}>
              Kích hoạt
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
