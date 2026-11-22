"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { fetchBoard, type BoardResponse } from "@/lib/api/opsBoard";
import { normalizeApiError } from "@/lib/errors";
import { useAuthStore } from "@/stores/authStore";

const SELECT_CLASS =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

const STATUSES = [
  "",
  "draft",
  "payment_pending",
  "paid",
  "sampling",
  "collected",
  "in_transit",
  "lab_received",
  "testing",
  "pending_review",
  "approved",
  "released",
  "cancelled",
];

const money = (n: number) => `${Math.round(n).toLocaleString("vi-VN")} ₫`;

function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

export function OperationsBoard() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<BoardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      setData(
        await fetchBoard(
          { token, organizationId },
          { status, q, date_from: dateFrom, date_to: dateTo, page },
        ),
      );
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [token, organizationId, status, q, dateFrom, dateTo, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const summary = data?.summary;
  const pages = data ? Math.max(1, Math.ceil(data.total_rows / data.page_size)) : 1;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card>
          <CardDescription>Số đơn</CardDescription>
          <CardTitle>{summary ? summary.orders : "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Giá trị đơn</CardDescription>
          <CardTitle>{summary ? money(summary.orders_value) : "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Đã thu</CardDescription>
          <CardTitle>{summary ? money(summary.collected) : "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Theo trạng thái</CardDescription>
          <p className="mt-1 text-sm text-slate-700">
            {summary && Object.keys(summary.by_status).length > 0
              ? Object.entries(summary.by_status)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(" · ")
              : "—"}
          </p>
        </Card>
      </div>

      <Card>
        <CardTitle>Danh sách đơn</CardTitle>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <div>
            <Label htmlFor="ob-q">Tìm mã đơn hoặc tên</Label>
            <Input
              id="ob-q"
              value={q}
              onChange={(e) => {
                setPage(1);
                setQ(e.target.value);
              }}
            />
          </div>
          <div>
            <Label htmlFor="ob-status">Trạng thái</Label>
            <select
              id="ob-status"
              className={SELECT_CLASS}
              value={status}
              onChange={(e) => {
                setPage(1);
                setStatus(e.target.value);
              }}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s === "" ? "Tất cả" : s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="ob-from">Từ ngày</Label>
            <Input
              id="ob-from"
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setPage(1);
                setDateFrom(e.target.value);
              }}
            />
          </div>
          <div>
            <Label htmlFor="ob-to">Đến ngày</Label>
            <Input
              id="ob-to"
              type="date"
              value={dateTo}
              onChange={(e) => {
                setPage(1);
                setDateTo(e.target.value);
              }}
            />
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="py-2 pr-4">Mã đơn</th>
                <th className="py-2 pr-4">Bệnh nhân</th>
                <th className="py-2 pr-4">Trạng thái</th>
                <th className="py-2 pr-4">Nguồn</th>
                <th className="py-2 pr-4 text-right">Tổng tiền</th>
                <th className="py-2">Tạo lúc</th>
              </tr>
            </thead>
            <tbody>
              {loading && !data ? (
                <tr>
                  <td className="py-3 text-slate-500" colSpan={6}>
                    Đang tải…
                  </td>
                </tr>
              ) : data && data.orders.length === 0 ? (
                <tr>
                  <td className="py-3 text-slate-500" colSpan={6}>
                    Không có đơn phù hợp.
                  </td>
                </tr>
              ) : (
                data?.orders.map((o) => (
                  <tr key={o.order_code} className="border-t border-slate-100">
                    <td className="py-2 pr-4 font-mono text-xs">{o.order_code}</td>
                    <td className="py-2 pr-4">{o.patient_name}</td>
                    <td className="py-2 pr-4">{o.status}</td>
                    <td className="py-2 pr-4">{o.source_org_name ?? "—"}</td>
                    <td className="py-2 pr-4 text-right">{money(o.total_amount)}</td>
                    <td className="py-2">{fmtTime(o.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex items-center gap-3 text-sm text-slate-600">
          <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Trước
          </Button>
          <span>
            Trang {page}/{pages} · {data?.total_rows ?? 0} đơn
          </span>
          <Button size="sm" variant="outline" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
            Sau
          </Button>
          <Button size="sm" variant="ghost" onClick={() => void load()}>
            Làm mới
          </Button>
        </div>
      </Card>
    </div>
  );
}
