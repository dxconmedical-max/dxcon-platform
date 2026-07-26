"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  fetchLabDashboard,
  fetchTestingQueue,
  type LabDashboard,
  type LabQueueRow,
} from "@/lib/api/labWorkflow";

import { DataState, SectionHeader, StatusPill } from "../_components/ui";

export default function LabQueuePage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );
  const [dash, setDash] = useState<LabDashboard | null>(null);
  const [rows, setRows] = useState<LabQueueRow[]>([]);
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
      const [d, q] = await Promise.all([fetchLabDashboard(auth), fetchTestingQueue(auth, { per_page: 50 })]);
      setDash(d);
      setRows(q.data);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AppShell title="Lab queue" workspacePath="/app/lab">
      <div className="space-y-6 p-4 md:p-6">
        <SectionHeader
          title="Laboratory worklist"
          description="Incoming, accessioned, and in-process specimens."
          actions={
            <>
              <Button size="sm" variant="outline" onClick={() => void load()}>
                Refresh
              </Button>
              <Link href="/app/lab/workflow">
                <Button size="sm">Open workflow</Button>
              </Link>
            </>
          }
        />

        {dash ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Incoming", dash.kpis.incoming],
              ["Received", dash.kpis.received],
              ["Testing", dash.kpis.testing],
              ["Pending review", dash.kpis.pending_review],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
              </div>
            ))}
          </div>
        ) : null}

        <DataState loading={loading} error={error} empty={!rows.length} emptyLabel="No lab worklist items." onRetry={() => void load()}>
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2">Order</th>
                  <th className="px-3 py-2">Patient</th>
                  <th className="px-3 py-2">Accession</th>
                  <th className="px-3 py-2">Test</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {rows.map((row) => (
                  <tr key={`${row.order_code}-${row.test_code}`} className="hover:bg-slate-50/80">
                    <td className="px-3 py-2 font-medium text-slate-900">{row.order_code}</td>
                    <td className="px-3 py-2 text-slate-700">{row.patient || row.patient_name || "—"}</td>
                    <td className="px-3 py-2 text-slate-700">{row.accession_number || "—"}</td>
                    <td className="px-3 py-2 text-slate-700">{row.test_name || row.test_code}</td>
                    <td className="px-3 py-2">
                      <StatusPill status={String(row.order_status || row.status || "—")} />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        className="text-sm font-medium text-sky-700 hover:underline"
                        href={`/app/lab/workflow?order=${encodeURIComponent(row.order_code)}`}
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </div>
    </AppShell>
  );
}
