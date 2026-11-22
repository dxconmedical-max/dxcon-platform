"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { fetchReport, type ReportResponse } from "@/lib/api/opsBoard";
import { normalizeApiError } from "@/lib/errors";
import { useAuthStore } from "@/stores/authStore";

const money = (n: number) => `${Math.round(n).toLocaleString("vi-VN")} ₫`;

export function OperationsReport() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [data, setData] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setData(await fetchReport({ token, organizationId }, from, to));
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, [token, organizationId, from, to]);

  useEffect(() => {
    void load();
  }, [load]);

  const max = Math.max(1, ...(data?.days ?? []).map((d) => d.orders_value));
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <Label htmlFor="rp-from">Từ ngày</Label>
          <Input id="rp-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="rp-to">Đến ngày</Label>
          <Input id="rp-to" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <Button variant="outline" onClick={() => void load()}>
          Làm mới
        </Button>
        <span className="text-xs text-slate-500">Mặc định 14 ngày gần nhất. Không tính đơn đã hủy.</span>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardDescription>Số đơn</CardDescription>
          <CardTitle>{data?.totals.orders ?? "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Giá trị đơn</CardDescription>
          <CardTitle>{data ? money(data.totals.orders_value) : "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Đã thu</CardDescription>
          <CardTitle>{data ? money(data.totals.collected) : "—"}</CardTitle>
        </Card>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr>
              <th className="py-2 pr-4">Ngày</th>
              <th className="py-2 pr-4">Số đơn</th>
              <th className="py-2 pr-4">Giá trị đơn</th>
              <th className="py-2 pr-4">Đã thu</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {(data?.days ?? []).map((d) => (
              <tr key={d.date} className="border-t border-slate-200">
                <td className="py-2 pr-4">{new Date(`${d.date}T00:00:00`).toLocaleDateString("vi-VN")}</td>
                <td className="py-2 pr-4">{d.orders}</td>
                <td className="py-2 pr-4">{money(d.orders_value)}</td>
                <td className="py-2 pr-4">{money(d.collected)}</td>
                <td className="w-40 py-2">
                  <div className="h-2 rounded bg-teal-600" style={{ width: `${(d.orders_value / max) * 100}%` }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
