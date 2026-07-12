"use client";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader, StatusPill } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchQuarantineQueue } from "@/lib/api/analyzer";

export default function LabQuarantinePage() {
  return (
    <WorkspaceScreen title="Quarantine" workspacePath="/app/lab/quarantine" permission="lab.read">
      {({ accessToken, organizationId }) => (
        <QuarantinePanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function QuarantinePanel({ accessToken, organizationId }: { accessToken: string; organizationId: string }) {
  const state = useSourcedData(
    () => fetchQuarantineQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const items = state.data?.items ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader title="Quarantine queue" description="Unmapped, duplicate, or invalid analyzer messages." source={state.source ?? undefined} />
      <DataState loading={state.loading} error={state.error} empty={items.length === 0} emptyLabel="Quarantine queue is empty." onRetry={state.reload}>
        <div className="space-y-2">
          {items.map((item) => (
            <Card key={item.id} className="flex items-center justify-between p-4 text-sm">
              <div>
                <p className="font-medium">{item.reason_code}</p>
                <p className="text-slate-500">{item.reason_detail ?? item.specimen_barcode}</p>
              </div>
              <StatusPill status={item.status} />
            </Card>
          ))}
        </div>
      </DataState>
    </div>
  );
}
