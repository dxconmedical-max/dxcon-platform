"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { listTestFlags, saveTestFlag, type TestFlagRow } from "@/lib/api/addons";

export default function TestFlagsPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<TestFlagRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);

  async function search() {
    if (!ctx) return;
    setBusy(true);
    setError(null);
    try {
      setRows(await listTestFlags(ctx, q.trim()));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  function patch(id: string, p: Partial<TestFlagRow>) {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...p } : r)));
  }

  async function save(r: TestFlagRow) {
    if (!ctx) return;
    setBusy(true);
    setError(null);
    setSaved(null);
    try {
      await saveTestFlag(ctx, r.id, {
        is_sendout: r.is_sendout,
        sendout_destination: r.sendout_destination ?? "",
        sendout_eta_days: r.sendout_eta_days,
        addon_window_hours: r.addon_window_hours,
      });
      setSaved(r.code);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Cấu hình xét nghiệm" workspacePath="/app/admin">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Gửi ngoài và thời hạn làm thêm</h1>
          <p className="text-sm text-slate-600">
            Đánh dấu xét nghiệm gửi nước ngoài/đơn vị khác (kèm số ngày trả dự kiến) và đặt số giờ cho phép làm thêm trên mẫu đã thu (để trống = 72 giờ).
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void search()}
            placeholder="Mã hoặc tên xét nghiệm"
            aria-label="Tìm xét nghiệm"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <Button disabled={busy} onClick={() => void search()}>Tìm</Button>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {saved ? <p className="text-sm text-green-700">Đã lưu {saved}.</p> : null}
        <ul className="space-y-3">
          {rows.map((r) => (
            <li key={r.id} className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <p className="font-medium">{r.name} ({r.code})</p>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={r.is_sendout} onChange={(e) => patch(r.id, { is_sendout: e.target.checked })} />
                Gửi ngoài / nước ngoài
              </label>
              <div className="flex flex-wrap gap-2 text-sm">
                <input
                  value={r.sendout_destination ?? ""}
                  onChange={(e) => patch(r.id, { sendout_destination: e.target.value })}
                  placeholder="Nơi gửi"
                  aria-label="Nơi gửi"
                  className="rounded-lg border border-slate-300 px-3 py-1.5"
                />
                <input
                  type="number"
                  min={1}
                  value={r.sendout_eta_days ?? ""}
                  onChange={(e) => patch(r.id, { sendout_eta_days: e.target.value ? Number(e.target.value) : null })}
                  placeholder="Số ngày trả"
                  aria-label="Số ngày trả kết quả dự kiến"
                  className="w-32 rounded-lg border border-slate-300 px-3 py-1.5"
                />
                <input
                  type="number"
                  min={1}
                  value={r.addon_window_hours ?? ""}
                  onChange={(e) => patch(r.id, { addon_window_hours: e.target.value ? Number(e.target.value) : null })}
                  placeholder="Giờ làm thêm"
                  aria-label="Số giờ cho phép làm thêm"
                  className="w-32 rounded-lg border border-slate-300 px-3 py-1.5"
                />
              </div>
              <Button size="sm" disabled={busy} onClick={() => void save(r)}>Lưu</Button>
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
