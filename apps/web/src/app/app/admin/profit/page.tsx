"use client";

import { useCallback, useEffect, useState } from "react";

import { MonthlyTrend, RankBars, moneyCaption } from "@/components/charts/ProfitCharts";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { formatVnd } from "@/lib/format";
import { downloadProfitExcel, getProfit, type ProfitReport, type ProfitRow } from "@/lib/api/labPayables";

const INPUT = "rounded-lg border border-slate-300 px-3 py-1.5 text-sm";

function Table({ title, rows }: { title: string; rows: ProfitRow[] }) {
  return (
    <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="font-medium">{title}</h2>
      {rows.length === 0 ? <p className="text-sm text-slate-500">Chưa có số liệu trong khoảng ngày này.</p> : null}
      {rows.length ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                <th className="py-1 pr-3">Tên</th>
                <th className="py-1 pr-3 text-right">Số ca</th>
                <th className="py-1 pr-3 text-right">Doanh thu</th>
                <th className="py-1 pr-3 text-right">Giá nhập</th>
                <th className="py-1 pr-3 text-right">Lãi</th>
                <th className="py-1 text-right">% lãi</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.label} className="border-t border-slate-100">
                  <td className="py-1 pr-3">
                    {r.label}
                    {r.missing_cost_orders ? <span className="block text-xs text-amber-700">{r.missing_cost_orders} ca thiếu giá nhập (chưa tính)</span> : null}
                  </td>
                  <td className="py-1 pr-3 text-right">{r.orders}</td>
                  <td className="py-1 pr-3 text-right">{formatVnd(r.sell)}</td>
                  <td className="py-1 pr-3 text-right">{formatVnd(r.cost)}</td>
                  <td className={`py-1 pr-3 text-right ${r.margin < 0 ? "text-red-700" : ""}`}>{formatVnd(r.margin)}</td>
                  <td className="py-1 text-right">{r.margin_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

export default function ProfitReportPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [data, setData] = useState<ProfitReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(
    async (s: string, e: string) => {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        const r = await getProfit({ token: accessToken, organizationId: activeOrganizationId }, s, e);
        setData(r);
        setStart(r.start);
        setEnd(r.end);
      } catch (err) {
        setError(normalizeApiError(err));
      } finally {
        setLoading(false);
      }
    },
    [accessToken, activeOrganizationId],
  );

  useEffect(() => {
    const timer = setTimeout(() => void load("", ""), 0);
    return () => clearTimeout(timer);
  }, [load]);

  return (
    <AppShell title="Báo cáo lãi" workspacePath="/app/admin">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Báo cáo lãi của DxCon</h1>
          <p className="text-sm text-slate-600">
            Lãi = giá bán cho khách trừ giá nhập từ phòng xét nghiệm, tính trên các ca đã gán phòng xét nghiệm và có đủ giá nhập. Mặc định là tháng này.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-xs">
            Từ ngày
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className={`${INPUT} block`} />
          </label>
          <label className="text-xs">
            Đến ngày
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className={`${INPUT} block`} />
          </label>
          <Button size="sm" disabled={loading} onClick={() => void load(start, end)}>
            Xem
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={loading || !accessToken}
            onClick={() =>
              accessToken &&
              void downloadProfitExcel({ token: accessToken, organizationId: activeOrganizationId }, start, end).catch((err) => setError(normalizeApiError(err)))
            }
          >
            Xuất Excel
          </Button>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {data ? (
          <>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {[
                ["Số ca", String(data.total.orders)],
                ["Doanh thu", formatVnd(data.total.sell)],
                ["Giá nhập", formatVnd(data.total.cost)],
                ["Lãi", `${formatVnd(data.total.margin)} (${data.total.margin_pct}%)`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl border border-slate-200 bg-white p-3">
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className="text-sm font-semibold">{value}</p>
                </div>
              ))}
            </div>
            {data.total.missing_cost_orders ? (
              <p className="text-sm text-amber-700">
                {data.total.missing_cost_orders} ca thiếu giá nhập nên chưa tính vào lãi. Nhập giá nhập ở màn Giá nhập & công nợ phải trả rồi bấm “Tính lại giá nhập các ca”.
              </p>
            ) : null}
            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="font-medium">Doanh thu và lãi theo tháng</h2>
              <MonthlyTrend rows={data.by_month} />
            </section>
            <div className="grid gap-4 md:grid-cols-2">
              <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
                <h2 className="font-medium">Phòng khám mang lại nhiều lãi nhất</h2>
                <RankBars rows={data.by_clinic} valueOf={(r) => r.margin} caption={moneyCaption} />
              </section>
              <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
                <h2 className="font-medium">Phòng xét nghiệm theo % lãi</h2>
                <RankBars rows={data.by_lab} valueOf={(r) => r.margin_pct} caption={(r) => `${r.margin_pct}% · ${formatVnd(r.margin)}`} />
              </section>
            </div>
            <Table title="Theo phòng khám / khách" rows={data.by_clinic} />
            <Table title="Theo phòng xét nghiệm" rows={data.by_lab} />
            <Table title="Theo tháng" rows={data.by_month} />
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
