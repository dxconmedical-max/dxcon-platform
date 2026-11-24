"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { listClinicOrders, type ClinicOrderCounts, type ClinicOrderSummary } from "@/lib/api/clinicResults";

const PROGRESS_VI = { released: "Đã có kết quả", in_progress: "Đang xử lý" } as const;

export default function ClinicReceptionDeskPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [items, setItems] = useState<ClinicOrderSummary[]>([]);
  const [counts, setCounts] = useState<ClinicOrderCounts | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let alive = true;
    void listClinicOrders({ token: accessToken, organizationId: activeOrganizationId })
      .then((r) => {
        if (!alive) return;
        setItems(r.items);
        setCounts(r.summary);
      })
      .catch((err) => alive && setError(normalizeApiError(err)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [accessToken, activeOrganizationId]);

  const needle = query.trim().toLowerCase();
  const visible = needle
    ? items.filter((o) => [o.patient_name, o.patient_code, o.order_code].join(" ").toLowerCase().includes(needle))
    : items;

  return (
    <AppShell title="Reception desk" workspacePath="/app/clinic">
      <div className="space-y-5">
        <div>
          <h1 className="text-xl font-semibold">Đơn xét nghiệm của phòng khám</h1>
          <p className="text-sm text-slate-600">
            Theo dõi các đơn của phòng khám anh/chị. Muốn tạo đơn mới, vui lòng liên hệ DxCon.
          </p>
        </div>
        {counts ? (
          <div className="grid gap-3 sm:grid-cols-4">
            {[
              ["Tổng số đơn", counts.total],
              ["Hôm nay", counts.today],
              ["Đang xử lý", counts.in_progress],
              ["Đã có kết quả", counts.released],
            ].map(([label, value]) => (
              <div key={label as string} className="rounded-xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-2 text-2xl font-semibold">{value}</p>
              </div>
            ))}
          </div>
        ) : null}
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tìm theo tên, mã bệnh nhân hoặc mã đơn"
          aria-label="Tìm đơn"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {!loading && visible.length === 0 && !error ? <p className="text-sm text-slate-500">Chưa có đơn nào.</p> : null}
        <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
          {visible.map((o) => (
            <li key={o.order_code} className="flex items-center justify-between gap-3 p-3 text-sm">
              <div className="min-w-0">
                <div className="truncate font-medium text-slate-900">{o.patient_name}</div>
                <div className="text-slate-500">
                  {o.patient_code} · {o.order_code} · {o.created_at ? new Date(o.created_at).toLocaleString("vi-VN") : ""}
                </div>
              </div>
              <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs ${o.progress === "released" ? "bg-teal-50 text-teal-800" : "bg-amber-50 text-amber-800"}`}>
                {PROGRESS_VI[o.progress]}
              </span>
            </li>
          ))}
        </ul>
        <Link href="/app/clinic-results" className="inline-block text-sm text-teal-700 underline">
          Xem kết quả đã trả →
        </Link>
      </div>
    </AppShell>
  );
}
