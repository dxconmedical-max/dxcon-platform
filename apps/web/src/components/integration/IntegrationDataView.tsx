"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { normalizeApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

type Row = Record<string, unknown>;

function findRows(payload: unknown): Row[] | null {
  if (Array.isArray(payload)) return payload.filter((x): x is Row => typeof x === "object" && x !== null);
  if (payload && typeof payload === "object") {
    for (const v of Object.values(payload as Row)) {
      const found = Array.isArray(v) ? findRows(v) : null;
      if (found && found.length > 0) return found;
    }
    const inner = (payload as Row).data;
    if (inner && typeof inner === "object" && !Array.isArray(inner)) return findRows(inner);
  }
  return null;
}

function cell(v: unknown): string {
  if (v == null) return "";
  if (typeof v === "object") return JSON.stringify(v).slice(0, 80);
  return String(v);
}

export function IntegrationDataView({
  title,
  description,
  endpoint,
}: {
  title: string;
  description: string;
  endpoint: string | null;
}) {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [payload, setPayload] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!token || !endpoint) return;
    setLoading(true);
    setError(null);
    try {
      setPayload(await apiRequest<unknown>(endpoint, { token, organizationId }));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [token, organizationId, endpoint]);

  useEffect(() => {
    void load();
  }, [load]);

  const rows = findRows(payload);
  const columns = rows && rows.length > 0 ? Object.keys(rows[0]).filter((k) => typeof rows[0][k] !== "object").slice(0, 7) : [];
  const flat =
    !rows && payload && typeof payload === "object"
      ? Object.entries((((payload as Row).data as Row) ?? (payload as Row)) as Row).filter(([, v]) => typeof v !== "object")
      : [];

  return (
    <AppShell title={title} workspacePath="/app/admin">
      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between gap-3">
          <p className="text-slate-600">{description}</p>
          <Button size="sm" variant="outline" onClick={() => void load()} disabled={loading || !endpoint}>
            Làm mới
          </Button>
        </div>
        {!endpoint ? (
          <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-slate-600">
            Mục này chưa có dữ liệu để hiển thị. Hiện chưa có kết nối ngoài nào được cấu hình.
          </p>
        ) : null}
        {error ? <p className="text-red-600">{error}</p> : null}
        {loading ? <p className="text-slate-500">Đang tải…</p> : null}
        {endpoint && !loading && !error && rows && rows.length === 0 ? (
          <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-slate-600">
            Chưa có dữ liệu. Chưa có hệ thống ngoài nào kết nối tới DxCon.
          </p>
        ) : null}
        {rows && rows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="text-slate-500">
                <tr>
                  {columns.map((c) => (
                    <th key={c} className="py-2 pr-4">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} className="border-t border-slate-200">
                    {columns.map((c) => (
                      <td key={c} className="py-2 pr-4">
                        {cell(row[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {!rows && flat.length > 0 ? (
          <dl className="grid max-w-xl grid-cols-2 gap-2">
            {flat.map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="text-slate-500">{k}</dt>
                <dd>{cell(v)}</dd>
              </div>
            ))}
          </dl>
        ) : null}
      </div>
    </AppShell>
  );
}
