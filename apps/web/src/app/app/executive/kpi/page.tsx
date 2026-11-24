"use client";

import { useEffect, useState } from "react";

import { CollectionPanel, LabTatPanel } from "@/components/charts/CollectionAndLabPanels";
import { MiniBars } from "@/components/charts/MiniBars";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { fetchExecutiveDashboard, type ExecutiveDashboard } from "@/lib/api/executive";
import { formatVnd, shortDate } from "@/lib/format";

function Tile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

export default function ExecutiveKpiPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [data, setData] = useState<ExecutiveDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    let alive = true;
    void fetchExecutiveDashboard({ token: accessToken, organizationId: activeOrganizationId })
      .then((d) => alive && setData(d))
      .catch((err) => alive && setError(normalizeApiError(err)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [accessToken, activeOrganizationId]);

  const w = data?.widgets;
  const lab = data?.charts.laboratory_performance;

  return (
    <AppShell title="Bảng KPI" workspacePath="/app/executive">
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Chỉ số điều hành</h1>
          <p className="text-sm text-slate-600">Số liệu thật từ hệ thống, cập nhật mỗi lần mở trang.</p>
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {w ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Tile label="Doanh thu hôm nay" value={formatVnd(w.revenue_today)} />
              <Tile label="Doanh thu tháng này" value={formatVnd(w.revenue_this_month)} />
              <Tile label="Đơn hôm nay" value={String(w.orders_today)} />
              <Tile label="Đơn tháng này" value={String(w.orders_this_month)} />
              <Tile label="Bệnh nhân" value={String(w.patients)} />
              <Tile label="Báo cáo chờ duyệt" value={String(w.pending_reports)} />
              <Tile label="Kết quả nguy kịch chưa xử lý" value={String(w.critical_results)} />
              <Tile
                label="TAT trung bình (đơn → trả kết quả)"
                value={lab?.tat_hours_avg != null ? `${lab.tat_hours_avg} giờ` : "Chưa có dữ liệu"}
                hint={
                  lab?.tat_hours_avg != null
                    ? `${lab.sample_size ?? 0} kết quả đã trả trong ${lab.window_days ?? 30} ngày qua`
                    : "Cần có kết quả đã trả trong 30 ngày qua"
                }
              />
            </div>
            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold">Số đơn 7 ngày gần đây</h2>
              <MiniBars
                label="Số đơn 7 ngày gần đây"
                points={data.charts.order_trend.map((p) => ({ label: shortDate(p.date), value: p.orders ?? 0 }))}
              />
            </section>
            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold">Doanh thu 7 ngày gần đây</h2>
              <MiniBars
                label="Doanh thu 7 ngày gần đây"
                format={(v) => (v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}tr` : `${Math.round(v / 1000)}k`)}
                points={data.charts.revenue_trend.map((p) => ({ label: shortDate(p.date), value: p.revenue ?? 0 }))}
              />
            </section>
            <div className="grid gap-4 lg:grid-cols-2">
              <LabTatPanel data={data.charts.lab_tat} />
              <CollectionPanel data={data.charts.collection_performance} />
            </div>
            <p className="text-xs text-slate-500">TAT từng lab và tỷ lệ lấy mẫu tính trong 30 ngày gần nhất.</p>
            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold">Xét nghiệm được chỉ định nhiều nhất</h2>
              {data.charts.top_tests.length === 0 ? (
                <p className="text-sm text-slate-500">Chưa có dữ liệu.</p>
              ) : (
                <ol className="space-y-1 text-sm">
                  {data.charts.top_tests.map((t) => (
                    <li key={t.test_name} className="flex justify-between gap-3">
                      <span className="truncate">{t.test_name}</span>
                      <span className="font-medium">{t.count}</span>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
