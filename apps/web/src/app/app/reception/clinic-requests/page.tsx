"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { formatBirth } from "@/lib/birth";
import { normalizeApiError } from "@/lib/errors";
import { approveSlip, listStaffSlips, rejectSlip, type ClinicSlip, type SlipStatus } from "@/lib/api/clinicOrders";

const STATUS_VI: Record<SlipStatus, string> = { NEW: "Chờ duyệt", APPROVED: "Đã tạo đơn", REJECTED: "Từ chối" };

export default function ClinicRequestsPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [filter, setFilter] = useState<SlipStatus>("NEW");
  const [items, setItems] = useState<ClinicSlip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<string | null>(null);
  const [reason, setReason] = useState("");

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setItems((await listStaffSlips({ token: accessToken, organizationId: activeOrganizationId }, filter)).items);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId, filter]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function act(id: string, fn: () => Promise<unknown>) {
    setBusyId(id);
    setError(null);
    try {
      await fn();
      setRejecting(null);
      setReason("");
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;

  return (
    <AppShell title="Phiếu từ phòng khám" workspacePath="/app/reception">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Phiếu chỉ định từ phòng khám</h1>
          <p className="text-sm text-slate-600">Kiểm tra họ tên, xét nghiệm và số ống mẫu, rồi bấm “Duyệt và tạo đơn”.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(["NEW", "APPROVED", "REJECTED"] as SlipStatus[]).map((s) => (
            <Button key={s} size="sm" variant={s === filter ? "primary" : "outline"} onClick={() => setFilter(s)}>
              {STATUS_VI[s]}
            </Button>
          ))}
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {!loading && items.length === 0 && !error ? <p className="text-sm text-slate-500">Không có phiếu nào.</p> : null}
        <ul className="space-y-3">
          {items.map((s) => (
            <li key={s.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <p className="font-medium">
                {s.patient_name} · sinh {formatBirth(s.birth_date, s.birth_year)}{s.birth_date ? "" : " (chỉ có năm)"}
              </p>
              <p className="text-sm text-slate-700">{s.tests.map((t) => `${t.name} (${t.code})`).join(", ")}</p>
              <p className="text-sm text-slate-600">
                {s.tube_count} ống mẫu · {s.organization_name ?? "Phòng khám"} · gửi bởi {s.requested_by ?? "—"}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                {s.reference} · {s.created_at ? new Date(s.created_at).toLocaleString("vi-VN") : ""}
                {s.order_code ? ` · đơn ${s.order_code}` : ""}
                {s.reject_reason ? ` · lý do từ chối: ${s.reject_reason}` : ""}
              </p>
              {s.status === "NEW" && ctx ? (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Button size="sm" disabled={busyId === s.id} onClick={() => void act(s.id, () => approveSlip(ctx, s.id))}>
                    {busyId === s.id ? "Đang tạo đơn…" : "Duyệt và tạo đơn"}
                  </Button>
                  {rejecting === s.id ? (
                    <>
                      <input
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Lý do từ chối"
                        aria-label="Lý do từ chối"
                        className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                      />
                      <Button size="sm" variant="outline" disabled={busyId === s.id || reason.trim().length < 3} onClick={() => void act(s.id, () => rejectSlip(ctx, s.id, reason.trim()))}>
                        Xác nhận từ chối
                      </Button>
                    </>
                  ) : (
                    <Button size="sm" variant="outline" onClick={() => setRejecting(s.id)}>
                      Từ chối
                    </Button>
                  )}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
