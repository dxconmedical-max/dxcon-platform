"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { fetchReleasedReportHtml } from "@/lib/api/labWorkflow";

import { SectionHeader } from "../../lab/_components/ui";

function PatientResultsPanel() {
  const { accessToken, activeOrganizationId } = useAuth();
  const searchParams = useSearchParams();
  const orderParam = searchParams.get("order");
  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const [orderCode, setOrderCode] = useState(orderParam || "");
  const [html, setHtml] = useState<string | null>(null);
  const [meta, setMeta] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !orderCode.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReleasedReportHtml(auth, orderCode.trim());
      setHtml(String(data.html_content || ""));
      setMeta(data);
    } catch (err) {
      setError(normalizeApiError(err));
      setHtml(null);
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth, orderCode]);

  useEffect(() => {
    if (orderParam) void load();
  }, [orderParam, load]);

  function download() {
    if (!html) return;
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${orderCode}-result.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="My released results"
        description="Download released laboratory reports. Email-ready notifications are issued at release."
        actions={
          <Link href="/app/patient" className="text-sm text-sky-700 hover:underline">
            Patient home
          </Link>
        }
      />
      <div className="flex flex-wrap gap-2">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="Order code"
          value={orderCode}
          onChange={(e) => setOrderCode(e.target.value)}
        />
        <Button disabled={loading || !orderCode.trim()} onClick={() => void load()}>
          {loading ? "Loading…" : "Open report"}
        </Button>
        <Button variant="outline" disabled={!html} onClick={download}>
          Download HTML/PDF
        </Button>
      </div>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {meta ? (
        <p className="text-xs text-slate-500">
          {String(meta.patient_name || "")} · {String(meta.result_code || "")} · Email ready:{" "}
          {String(meta.email_ready ?? true)}
        </p>
      ) : null}
      {html ? (
        <div
          className="rounded-xl border border-slate-200 bg-white p-4"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : null}
    </div>
  );
}

export default function PatientResultsPage() {
  return (
    <AppShell title="Patient results" workspacePath="/app/patient">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <PatientResultsPanel />
      </Suspense>
    </AppShell>
  );
}
