"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  DEMO_STATUSES,
  listDemoRequests,
  setDemoStatus,
  type DemoRequestItem,
  type DemoStatus,
} from "@/lib/api/publicDemo";

const STATUS_VI: Record<DemoStatus, string> = {
  NEW: "Mới",
  CONTACTED: "Đã liên hệ",
  DONE: "Hoàn tất",
  SPAM: "Spam",
};

export default function DemoRequestsPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [filter, setFilter] = useState<DemoStatus>("NEW");
  const [items, setItems] = useState<DemoRequestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await listDemoRequests({ token: accessToken, organizationId: activeOrganizationId }, filter);
      setItems(data.items);
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

  async function update(id: string, status: DemoStatus) {
    if (!accessToken) return;
    setBusyId(id);
    setError(null);
    try {
      await setDemoStatus({ token: accessToken, organizationId: activeOrganizationId }, id, status);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell title="Yêu cầu demo" workspacePath="/app/admin">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Yêu cầu demo từ website</h1>
          <p className="text-sm text-slate-600">
            Khách gửi từ biểu mẫu “Đặt lịch demo” trên trang chủ. Liên hệ lại rồi đổi trạng thái.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_STATUSES.map((status) => (
            <Button
              key={status}
              size="sm"
              variant={status === filter ? "primary" : "outline"}
              onClick={() => setFilter(status)}
            >
              {STATUS_VI[status]}
            </Button>
          ))}
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {!loading && items.length === 0 && !error ? (
          <p className="text-sm text-slate-500">Không có yêu cầu nào ở trạng thái “{STATUS_VI[filter]}”.</p>
        ) : null}
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium">
                    {item.full_name}
                    {item.organization ? ` · ${item.organization}` : ""}
                  </p>
                  <p className="text-sm text-slate-600">
                    <a className="text-teal-700" href={`mailto:${item.email}`}>{item.email}</a>
                    {item.phone ? (
                      <>
                        {" · "}
                        <a className="text-teal-700" href={`tel:${item.phone}`}>{item.phone}</a>
                      </>
                    ) : null}
                  </p>
                  {item.message ? (
                    <p className="mt-1 whitespace-pre-line break-words text-sm text-slate-700">{item.message}</p>
                  ) : null}
                  <p className="mt-1 text-xs text-slate-400">
                    {item.reference} · {item.created_at ? new Date(item.created_at).toLocaleString("vi-VN") : ""}
                    {item.handled_by ? ` · xử lý bởi ${item.handled_by}` : ""}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {DEMO_STATUSES.filter((s) => s !== item.status).map((s) => (
                    <Button key={s} size="sm" variant="outline" disabled={busyId === item.id} onClick={() => void update(item.id, s)}>
                      {STATUS_VI[s]}
                    </Button>
                  ))}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
