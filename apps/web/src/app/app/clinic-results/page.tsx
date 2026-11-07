"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import {
  getClinicReport,
  listClinicReports,
  type ClinicReportDetail,
  type ClinicReportSummary,
} from "@/lib/api/clinicResults";
import { normalizeApiError } from "@/lib/errors";

function formatDate(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString("vi-VN");
}

function ClinicResultsPanel() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [items, setItems] = useState<ClinicReportSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opening, setOpening] = useState<string | null>(null);
  const [report, setReport] = useState<ClinicReportDetail | null>(null);
  const requested = useRef(false);

  useEffect(() => {
    if (!accessToken || requested.current) return;
    requested.current = true;
    void listClinicReports({ token: accessToken, organizationId: activeOrganizationId })
      .then((result) => {
        setItems(result.items);
        setTotal(result.total);
      })
      .catch((err) => setError(normalizeApiError(err)))
      .finally(() => setLoading(false));
  }, [accessToken, activeOrganizationId]);

  const open = useCallback(
    (orderCode: string) => {
      if (!accessToken) return;
      setOpening(orderCode);
      setError(null);
      void getClinicReport({ token: accessToken, organizationId: activeOrganizationId }, orderCode)
        .then((detail) => setReport(detail))
        .catch((err) => setError(normalizeApiError(err)))
        .finally(() => setOpening(null));
    },
    [accessToken, activeOrganizationId],
  );

  if (!accessToken) {
    return <p className="text-sm text-slate-500">Đang tải phiên đăng nhập…</p>;
  }

  const needle = query.trim().toLowerCase();
  const visible = needle
    ? items.filter((r) =>
        [r.patient_name, r.patient_code, r.order_code]
          .join(" ")
          .toLowerCase()
          .includes(needle),
      )
    : items;

  if (report) {
    return (
      <div className="space-y-4">
        <button
          type="button"
          className="text-sm text-sky-700 underline"
          onClick={() => setReport(null)}
        >
          ← Quay lại danh sách
        </button>
        <div className="text-sm text-slate-700">
          <strong>{report.patient_name}</strong> · {report.patient_code} · {report.order_code} ·{" "}
          {formatDate(report.released_at)}
        </div>
        {/* sandbox="" : không chạy script, không gửi form, không truy cập trang cha */}
        <iframe
          title={`Kết quả ${report.order_code}`}
          sandbox=""
          srcDoc={report.html_content}
          className="h-[80vh] w-full rounded-xl border border-slate-200 bg-white"
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Kết quả xét nghiệm</h2>
        <p className="text-sm text-slate-500">
          Chỉ hiển thị kết quả đã được DxCon duyệt và trả cho phòng khám của anh/chị.
        </p>
      </div>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Tìm theo tên, mã bệnh nhân hoặc mã đơn"
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        aria-label="Tìm kết quả"
      />
      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      ) : null}
      {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
      {!loading && visible.length === 0 && !error ? (
        <p className="text-sm text-slate-500">Chưa có kết quả nào.</p>
      ) : null}
      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
        {visible.map((r) => (
          <li key={r.result_code} className="flex items-center justify-between gap-3 p-3">
            <div className="min-w-0 text-sm">
              <div className="truncate font-medium text-slate-900">{r.patient_name}</div>
              <div className="text-slate-500">
                {r.patient_code} · {r.order_code} · {formatDate(r.released_at)}
              </div>
            </div>
            <button
              type="button"
              disabled={opening === r.order_code}
              onClick={() => open(r.order_code)}
              className="shrink-0 rounded-lg bg-sky-700 px-3 py-1.5 text-sm text-white disabled:opacity-50"
            >
              {opening === r.order_code ? "Đang mở…" : "Xem"}
            </button>
          </li>
        ))}
      </ul>
      <p className="text-xs text-slate-400">Tổng: {total} kết quả</p>
    </div>
  );
}

export default function ClinicResultsPage() {
  return (
    <AppShell title="Kết quả xét nghiệm" workspacePath="/app/clinic-results">
      <ClinicResultsPanel />
    </AppShell>
  );
}
