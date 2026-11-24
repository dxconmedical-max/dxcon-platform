"use client";

import { useCallback, useEffect, useState } from "react";

import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { listClinicSettings, setClinicSetting, type ClinicSetting } from "@/lib/api/clinicOrders";

export default function ClinicSettingsPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [items, setItems] = useState<ClinicSetting[]>([]);
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
      setItems(await listClinicSettings({ token: accessToken, organizationId: activeOrganizationId }));
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

  async function toggle(c: ClinicSetting) {
    if (!accessToken) return;
    setBusyId(c.id);
    setError(null);
    try {
      await setClinicSetting({ token: accessToken, organizationId: activeOrganizationId }, c.id, !c.enabled);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell title="Phòng khám tự chỉ định" workspacePath="/app/admin">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Phòng khám được tự chỉ định</h1>
          <p className="text-sm text-slate-600">Bật cho phòng khám nào, phòng khám đó mới gửi được phiếu chỉ định. Mặc định là tắt.</p>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {!loading && items.length === 0 && !error ? <p className="text-sm text-slate-500">Chưa có phòng khám nào.</p> : null}
        <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
          {items.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-3 p-3 text-sm">
              <div>
                <p className="font-medium">{c.name}</p>
                <p className="text-slate-500">{c.code} · {c.enabled ? "Đang bật" : "Đang tắt"}</p>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  href={`/app/admin/clinic-billing?clinic=${encodeURIComponent(c.id)}`}
                  className="text-sm font-medium text-teal-700 underline"
                >
                  Hợp đồng & giá
                </Link>
                <Button size="sm" variant={c.enabled ? "outline" : "primary"} disabled={busyId === c.id} onClick={() => void toggle(c)}>
                  {c.enabled ? "Tắt" : "Bật"}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
