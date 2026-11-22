"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { Label } from "@/components/ui/Input";
import {
  fetchBoardCollections,
  type BoardCollection,
  type CollectionsResponse,
} from "@/lib/api/opsBoard";
import {
  assignCollector,
  fetchAssignableCollectors,
  unassignCollector,
  type AssignableCollector,
} from "@/lib/api/sampleCollection";
import { normalizeApiError } from "@/lib/errors";
import { useAuthStore } from "@/stores/authStore";

const SELECT_CLASS =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

const FINAL = new Set(["COLLECTED", "DISPATCHED", "HANDED_OFF", "ARRIVED_AT_LAB", "REJECTED", "CANCELLED", "VERIFIED"]);

function when(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

export function OperationsCollections() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [data, setData] = useState<CollectionsResponse | null>(null);
  const [collectors, setCollectors] = useState<AssignableCollector[]>([]);
  const [pick, setPick] = useState<Record<string, string>>({});
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setData(await fetchBoardCollections({ token, organizationId }, status));
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, [token, organizationId, status]);

  useEffect(() => {
    void load();
    const t = setInterval(() => void load(), 15000);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    if (!token) return;
    fetchAssignableCollectors({ token, organizationId })
      .then(setCollectors)
      .catch(() => setCollectors([]));
  }, [token, organizationId]);

  async function assign(row: BoardCollection) {
    const collectorId = pick[row.id] || collectors[0]?.id;
    if (!collectorId) {
      setError("Chưa có tài khoản người lấy mẫu để gán.");
      return;
    }
    const c = collectors.find((x) => x.id === collectorId);
    setBusy(row.id);
    try {
      await assignCollector({ token, organizationId }, row.id, {
        collector_id: collectorId,
        collector_name: c?.full_name || c?.email,
      });
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  async function release(row: BoardCollection) {
    setBusy(row.id);
    try {
      await unassignCollector({ token, organizationId }, row.id);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  const s = data?.summary;
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardDescription>Yêu cầu lấy mẫu</CardDescription>
          <CardTitle>{s?.total ?? "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Chưa gán người</CardDescription>
          <CardTitle className={s && s.unassigned > 0 ? "text-red-600" : ""}>{s?.unassigned ?? "—"}</CardTitle>
        </Card>
        <Card>
          <CardDescription>Tự làm mới mỗi 15 giây</CardDescription>
          <div className="mt-1">
            <Label htmlFor="col-status">Lọc trạng thái</Label>
            <select id="col-status" className={SELECT_CLASS} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Tất cả</option>
              {Object.keys(s?.by_status ?? {}).map((k) => (
                <option key={k} value={k}>
                  {k} ({s?.by_status[k]})
                </option>
              ))}
            </select>
          </div>
        </Card>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr>
              <th className="py-2 pr-3">Đơn</th>
              <th className="py-2 pr-3">Khách / địa chỉ</th>
              <th className="py-2 pr-3">Hẹn</th>
              <th className="py-2 pr-3">Trạng thái</th>
              <th className="py-2 pr-3">Người lấy mẫu</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {!data ? (
              <tr>
                <td className="py-4 text-slate-500" colSpan={6}>
                  Đang tải…
                </td>
              </tr>
            ) : data.items.length === 0 ? (
              <tr>
                <td className="py-4 text-slate-500" colSpan={6}>
                  Chưa có yêu cầu lấy mẫu tại nhà.
                </td>
              </tr>
            ) : (
              data.items.map((r) => (
                <tr key={r.id} className="border-t border-slate-200 align-top">
                  <td className="py-2 pr-3 font-mono text-xs">{r.order_code ?? "—"}</td>
                  <td className="py-2 pr-3">
                    {r.patient_name ?? "—"}
                    <div className="text-xs text-slate-500">
                      {[r.address, r.contact_phone].filter(Boolean).join(" · ")}
                    </div>
                  </td>
                  <td className="py-2 pr-3 text-xs">
                    {[r.requested_date, r.time_window].filter(Boolean).join(" ") || "—"}
                  </td>
                  <td className="py-2 pr-3 text-xs">{r.status}</td>
                  <td className="py-2 pr-3">
                    {r.collector_name ? (
                      <>
                        {r.collector_name}
                        <div className={`text-xs ${r.collector_online ? "text-emerald-700" : "text-slate-400"}`}>
                          {r.collector_online ? `Đang chia sẻ vị trí (${when(r.collector_last_seen)})` : "Không chia sẻ vị trí"}
                        </div>
                      </>
                    ) : (
                      <span className="text-red-600">Chưa gán</span>
                    )}
                  </td>
                  <td className="py-2">
                    {FINAL.has(r.status) ? null : (
                      <div className="flex items-center gap-2">
                        <select
                          aria-label="Chọn người lấy mẫu"
                          className={SELECT_CLASS}
                          value={pick[r.id] ?? ""}
                          onChange={(e) => setPick((p) => ({ ...p, [r.id]: e.target.value }))}
                        >
                          <option value="">Chọn…</option>
                          {collectors.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.full_name || c.email}
                            </option>
                          ))}
                        </select>
                        <Button size="sm" disabled={busy === r.id || !pick[r.id]} onClick={() => void assign(r)}>
                          {r.collector_id ? "Đổi" : "Gán"}
                        </Button>
                        {r.collector_id ? (
                          <Button size="sm" variant="ghost" disabled={busy === r.id} onClick={() => void release(r)}>
                            Bỏ gán
                          </Button>
                        ) : null}
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
