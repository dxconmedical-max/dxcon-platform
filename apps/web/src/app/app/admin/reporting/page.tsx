"use client";

import { useCallback, useEffect, useState } from "react";

import { CollectionPanel, LabTatPanel } from "@/components/charts/CollectionAndLabPanels";
import { MiniBars } from "@/components/charts/MiniBars";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { fetchReportSummary, type ReportSummary } from "@/lib/api/executive";
import { formatVnd, shortDate } from "@/lib/format";

function isoDay(d: Date): string {
  const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return z.toISOString().slice(0, 10);
}

function csvOf(report: ReportSummary): string {
  const rows = [["Ngày", "Số đơn", "Doanh thu"], ...report.daily.map((d) => [d.date, String(d.orders), String(d.revenue)])];
  rows.push([], ["Xét nghiệm", "Số lượng", "Doanh thu"]);
  report.top_tests.forEach((t) => rows.push([`"${t.test_name.replace(/"/g, '""')}"`, String(t.quantity), String(t.revenue)]));
  return "﻿" + rows.map((r) => r.join(",")).join("\n");
}

export default function ReportingPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const today = isoDay(new Date());
  const [from, setFrom] = useState(isoDay(new Date(Date.now() - 29 * 86400000)));
  const [to, setTo] = useState(today);
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await fetchReportSummary({ token: accessToken, organizationId: activeOrganizationId }, { from, to }));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId, from, to]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  function download() {
    if (!report) return;
    const blob = new Blob([csvOf(report)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dxcon-bao-cao-${report.period_start}_${report.period_end}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AppShell title="Reporting" workspacePath="/app/admin">
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Báo cáo</h1>
          <p className="text-sm text-slate-600">Đơn hàng, doanh thu và xét nghiệm theo khoảng ngày.</p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">
            Từ ngày
            <input type="date" value={from} max={to} onChange={(e) => setFrom(e.target.value)} className="mt-1 block rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </label>
          <label className="text-sm">
            Đến ngày
            <input type="date" value={to} min={from} max={today} onChange={(e) => setTo(e.target.value)} className="mt-1 block rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </label>
          <Button variant="outline" onClick={download} disabled={!report}>
            Tải CSV
          </Button>
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {report ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">Tổng số đơn</p>
                <p className="mt-2 text-2xl font-semibold">{report.orders_total}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">Doanh thu đã thu</p>
                <p className="mt-2 text-2xl font-semibold">{formatVnd(report.revenue_total)}</p>
              </div>
            </div>
            {report.daily.length <= 31 ? (
              <section className="rounded-xl border border-slate-200 bg-white p-4">
                <h2 className="mb-3 text-sm font-semibold">Số đơn theo ngày</h2>
                <MiniBars label="Số đơn theo ngày" points={report.daily.map((d) => ({ label: shortDate(d.date), value: d.orders }))} />
              </section>
            ) : null}
            <div className="grid gap-4 md:grid-cols-2">
              <section className="rounded-xl border border-slate-200 bg-white p-4">
                <h2 className="mb-2 text-sm font-semibold">Theo trạng thái</h2>
                <ul className="space-y-1 text-sm">
                  {report.orders_by_status.length === 0 ? <li className="text-slate-500">Chưa có dữ liệu.</li> : null}
                  {report.orders_by_status.map((s) => (
                    <li key={s.status} className="flex justify-between"><span>{s.status}</span><b>{s.count}</b></li>
                  ))}
                </ul>
              </section>
              <section className="rounded-xl border border-slate-200 bg-white p-4">
                <h2 className="mb-2 text-sm font-semibold">Theo nguồn đơn</h2>
                <ul className="space-y-1 text-sm">
                  {report.orders_by_source.length === 0 ? <li className="text-slate-500">Chưa có dữ liệu.</li> : null}
                  {report.orders_by_source.map((s) => (
                    <li key={s.source} className="flex justify-between"><span>{s.source}</span><b>{s.count}</b></li>
                  ))}
                </ul>
              </section>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <LabTatPanel data={report.lab_tat} />
              <CollectionPanel data={report.collection} />
            </div>
            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="mb-2 text-sm font-semibold">Xét nghiệm nhiều nhất</h2>
              {report.top_tests.length === 0 ? (
                <p className="text-sm text-slate-500">Chưa có dữ liệu.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500"><th className="py-1">Xét nghiệm</th><th className="py-1 text-right">Số lượng</th><th className="py-1 text-right">Doanh thu</th></tr>
                  </thead>
                  <tbody>
                    {report.top_tests.map((t) => (
                      <tr key={t.test_name} className="border-t border-slate-100">
                        <td className="py-1">{t.test_name}</td>
                        <td className="py-1 text-right">{t.quantity}</td>
                        <td className="py-1 text-right">{formatVnd(t.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
