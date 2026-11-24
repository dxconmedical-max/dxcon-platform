"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  importCatalog,
  parseCatalogCsv,
  type CatalogRow,
  type ImportSummary,
} from "@/lib/api/testCatalogImport";

export default function AdminTestCatalogImportPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [rows, setRows] = useState<CatalogRow[]>([]);
  const [fileName, setFileName] = useState("");
  const [removeDemo, setRemoveDemo] = useState(true);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onFile(file: File | undefined) {
    setSummary(null);
    setError(null);
    setRows([]);
    if (!file) return;
    setFileName(file.name);
    const parsed = parseCatalogCsv(await file.text());
    if (parsed.error) {
      setError(parsed.error);
      return;
    }
    setRows(parsed.rows);
  }

  async function run(apply: boolean) {
    if (!accessToken || rows.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const result = await importCatalog(
        { token: accessToken, organizationId: activeOrganizationId },
        rows,
        { apply, removeDemo },
      );
      setSummary(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Nhập danh mục xét nghiệm" workspacePath="/app/admin">
      <div className="max-w-3xl space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Nhập danh mục xét nghiệm</h1>
          <p className="text-sm text-slate-600">
            Tải file CSV (UTF-8) có 5 cột: <code>code, name, category, sample_type, price</code>. Hệ thống thêm mới
            hoặc cập nhật theo <code>code</code>. Bấm Xem trước trước, kiểm tra số liệu rồi mới Áp dụng.
          </p>
        </div>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => void onFile(event.target.files?.[0])}
          className="block text-sm"
        />
        {rows.length > 0 ? (
          <p className="text-sm text-slate-700">
            Đã đọc <strong>{rows.length}</strong> dòng từ {fileName}.
          </p>
        ) : null}
        <label className="flex items-start gap-2 text-sm text-slate-700">
          <input type="checkbox" className="mt-1" checked={removeDemo} onChange={(e) => setRemoveDemo(e.target.checked)} />
          <span>Xóa các xét nghiệm demo (mã bắt đầu bằng <code>DEMO-TST-</code>) khi áp dụng.</span>
        </label>
        <div className="flex gap-2">
          <Button variant="outline" disabled={busy || rows.length === 0} onClick={() => void run(false)}>
            Xem trước
          </Button>
          <Button
            disabled={busy || rows.length === 0 || !summary || summary.applied}
            onClick={() => void run(true)}
          >
            Áp dụng
          </Button>
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {summary ? (
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
            <p className="font-medium">{summary.applied ? "Đã áp dụng" : "Xem trước (chưa thay đổi gì)"}</p>
            <ul className="mt-2 space-y-1 text-slate-700">
              <li>Thêm mới: {summary.create}</li>
              <li>Cập nhật: {summary.update}</li>
              <li>Không đổi: {summary.unchanged}</li>
              <li>
                Xét nghiệm demo: {summary.demo_present} đang có
                {removeDemo ? `, sẽ xóa ${summary.demo_to_remove}` : ", giữ lại"}
              </li>
            </ul>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
