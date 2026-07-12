"use client";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchResultReview } from "@/lib/api/analyzer";

export default function LabResultsReviewPage() {
  return (
    <WorkspaceScreen title="Result review" workspacePath="/app/lab/results-review" permission="lab.read">
      {({ accessToken, organizationId }) => (
        <ResultsReviewPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function ResultsReviewPanel({ accessToken, organizationId }: { accessToken: string; organizationId: string }) {
  const state = useSourcedData(
    () => fetchResultReview({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const results = state.data?.results ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Incoming results"
        description="Preliminary analyzer results pending technician review. Results are never auto-released."
        source={state.source ?? undefined}
      />
      <DataState loading={state.loading} error={state.error} empty={results.length === 0} emptyLabel="No preliminary results awaiting review." onRetry={state.reload}>
        <div className="space-y-2">
          {results.map((r) => (
            <Card key={r.id} className="p-4 text-sm">
              <p className="font-medium">{r.specimen_barcode} — {r.test_code}</p>
              <p>Original: {r.original_value} {r.unit ?? ""}</p>
              <p className="text-slate-500">Status: {r.review_status}</p>
            </Card>
          ))}
        </div>
      </DataState>
    </div>
  );
}
