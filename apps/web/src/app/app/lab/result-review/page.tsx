"use client";

import Link from "next/link";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchTechnicianQueue } from "@/lib/api/clinical";

export default function LabResultReviewPage() {
  return (
    <WorkspaceScreen title="Result review" workspacePath="/app/lab/result-review" permission="lab.read">
      {({ accessToken, organizationId }) => (
        <ResultReviewPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function ResultReviewPanel({ accessToken, organizationId }: { accessToken: string; organizationId: string }) {
  const state = useSourcedData(
    () => fetchTechnicianQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const prelim = state.data?.preliminary_analyzer ?? [];
  const pending = state.data?.result_items_pending ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Technician review queue"
        description="Analyzer and result items pending validation. Results are never auto-released."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={prelim.length === 0 && pending.length === 0}
        emptyLabel="No results awaiting technician review."
        onRetry={state.reload}
      >
        {pending.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-700">Result items</h3>
            {pending.map((r) => (
              <Card key={String(r.id)} className="flex items-center justify-between p-4 text-sm">
                <div>
                  <p className="font-medium">{String(r.test_code ?? r.test_name)}</p>
                  <p>Status: {String(r.result_status ?? "PENDING")}</p>
                </div>
                <Link href={`/app/lab/result-review/${encodeURIComponent(String(r.id))}`}>
                  <Button size="sm" variant="outline">
                    Review
                  </Button>
                </Link>
              </Card>
            ))}
          </div>
        )}
        {prelim.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-700">Preliminary analyzer results</h3>
            {prelim.map((r) => (
              <Card key={String(r.id)} className="p-4 text-sm">
                <p className="font-medium">{String(r.specimen_barcode ?? "—")} — {String(r.test_code ?? "")}</p>
                <p>Original: {String(r.original_value ?? "")}</p>
              </Card>
            ))}
          </div>
        )}
      </DataState>
    </div>
  );
}
