"use client";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader, StatusPill } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchAnalyzerDashboard, fetchAnalyzers } from "@/lib/api/analyzer";

export default function LabAnalyzersPage() {
  return (
    <WorkspaceScreen title="Analyzers" workspacePath="/app/lab/analyzers" permission="lab.read">
      {({ accessToken, organizationId }) => (
        <AnalyzersPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function AnalyzersPanel({ accessToken, organizationId }: { accessToken: string; organizationId: string }) {
  const ctx = { token: accessToken, organizationId };
  const dash = useSourcedData(() => fetchAnalyzerDashboard(ctx), [accessToken, organizationId]);
  const list = useSourcedData(() => fetchAnalyzers(ctx), [accessToken, organizationId]);
  const kpis = dash.data?.kpis;

  return (
    <div className="space-y-4">
      <SectionHeader title="Analyzer dashboard" description="Instrument health and integration status." source={dash.source ?? undefined} />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Online", kpis?.analyzers_online],
          ["Pending review", kpis?.pending_review],
          ["Quarantine", kpis?.quarantine_open],
          ["Worklist queued", kpis?.worklist_queued],
        ].map(([label, value]) => (
          <Card key={String(label)} className="p-4">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-2xl font-semibold">{value ?? "—"}</p>
          </Card>
        ))}
      </div>
      <DataState loading={list.loading} error={list.error} empty={(list.data?.analyzers.length ?? 0) === 0} emptyLabel="No analyzers registered." onRetry={list.reload}>
        <div className="space-y-2">
          {(list.data?.analyzers ?? []).map((a) => (
            <Card key={a.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{a.name}</p>
                <p className="text-xs text-slate-500">{a.analyzer_code} · {a.protocol ?? "—"}</p>
              </div>
              <StatusPill status={a.status} />
            </Card>
          ))}
        </div>
      </DataState>
    </div>
  );
}
