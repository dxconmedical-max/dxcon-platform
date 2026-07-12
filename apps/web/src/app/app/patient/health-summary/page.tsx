"use client";

import { Sparkles } from "lucide-react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchHealthSummary, type HealthSummary } from "@/lib/api/patient-portal";

function HealthSummaryPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<HealthSummary>(
    () => fetchHealthSummary({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const summary = state.data;

  return (
    <div className="space-y-4">
      <SectionHeader
        title="AI health summary"
        description="A plain-language overview of your recent results."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={!summary}
        emptyLabel="No health summary available yet."
        onRetry={state.reload}
      >
        {summary ? (
          <div className="space-y-4">
            <Card className="space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-teal-600" />
                <Badge tone="info">AI-assisted — requires clinician review</Badge>
              </div>
              <p className="text-lg font-medium text-slate-900">{summary.headline}</p>
              <p className="text-xs text-slate-400">Generated {summary.generated_at}</p>
            </Card>

            <Card>
              <h3 className="text-sm font-semibold text-slate-900">Highlights</h3>
              <ul className="mt-3 space-y-2">
                {summary.highlights.map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-slate-700">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="border-amber-200 bg-amber-50/60">
              <h3 className="text-sm font-semibold text-amber-900">Recommendation</h3>
              <p className="mt-2 text-sm text-amber-900">{summary.recommendation}</p>
            </Card>
          </div>
        ) : null}
      </DataState>
    </div>
  );
}

export default function PatientHealthSummaryPage() {
  return (
    <WorkspaceScreen title="Health summary" workspacePath="/app/patient" permission="portal.patient.read">
      {(ctx) => <HealthSummaryPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
