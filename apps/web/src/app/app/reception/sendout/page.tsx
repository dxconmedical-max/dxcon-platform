"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { listSendout, updateSendout, type SendoutItem, type SendoutStatus } from "@/lib/api/addons";

const LABEL: Record<SendoutStatus, string> = { OVERDUE: "Quá hạn", DUE_SOON: "Sắp đến hạn", WAITING: "Đang chờ" };
const TONE: Record<SendoutStatus, string> = {
  OVERDUE: "bg-red-100 text-red-800",
  DUE_SOON: "bg-amber-100 text-amber-800",
  WAITING: "bg-slate-100 text-slate-700",
};

export default function SendoutPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;
  const [items, setItems] = useState<SendoutItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setItems((await listSendout({ token: accessToken, organizationId: activeOrganizationId })).items);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function act(it: SendoutItem, body: Parameters<typeof updateSendout>[3]) {
    if (!ctx) return;
    const key = `${it.order_code}/${it.test_code}`;
    setBusy(key);
    setError(null);
    try {
      await updateSendout(ctx, it.order_code, it.test_code, body);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <AppShell title="Xét nghiệm gửi ngoài" workspacePath="/app/reception">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Nhắc nhập kết quả xét nghiệm gửi ngoài</h1>
          <p className="text-sm text-slate-600">
            Danh sách xét nghiệm gửi nước ngoài hoặc đơn vị khác chưa có kết quả, kèm ngày trả dự kiến. Khi kết quả về, nhập kết quả vào đơn thì mục này tự biến mất.
          </p>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {!loading && items.length === 0 && !error ? <p className="text-sm text-slate-500">Không có xét nghiệm gửi ngoài nào đang chờ.</p> : null}
        <ul className="space-y-3">
          {items.map((it) => (
            <li key={`${it.order_code}/${it.test_code}`} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${TONE[it.status]}`}>{LABEL[it.status]}</span>
                <p className="font-medium">{it.test_name} · {it.patient_name}</p>
              </div>
              <p className="text-sm text-slate-600">
                Đơn {it.order_code} · {it.destination ?? "chưa ghi nơi gửi"} · dự kiến {it.eta_date}
                {it.days_left < 0 ? ` (trễ ${-it.days_left} ngày)` : it.days_left === 0 ? " (hôm nay)" : ` (còn ${it.days_left} ngày)`}
              </p>
              {it.sent_at ? <p className="text-xs text-slate-400">Đã gửi ngày {it.sent_at}</p> : null}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <label className="text-xs text-slate-500">
                  Ngày gửi{" "}
                  <input
                    type="date"
                    defaultValue={it.sent_at ?? ""}
                    onBlur={(e) => e.target.value && e.target.value !== it.sent_at && void act(it, { sent_at: e.target.value })}
                    className="rounded border border-slate-300 px-2 py-1 text-sm"
                  />
                </label>
                <label className="text-xs text-slate-500">
                  Trả dự kiến{" "}
                  <input
                    type="date"
                    defaultValue={it.eta_date}
                    onBlur={(e) => e.target.value && e.target.value !== it.eta_date && void act(it, { eta_date: e.target.value })}
                    className="rounded border border-slate-300 px-2 py-1 text-sm"
                  />
                </label>
                <Button size="sm" variant="outline" disabled={busy === `${it.order_code}/${it.test_code}`} onClick={() => void act(it, { dismissed: true })}>
                  Bỏ nhắc
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
