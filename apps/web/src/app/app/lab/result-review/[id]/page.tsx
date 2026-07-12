"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchTechnicianResult, rejectResult, validateResult } from "@/lib/api/clinical";

export default function LabResultReviewDetailPage() {
  const params = useParams();
  const itemId = String(params.id ?? "");
  return (
    <WorkspaceScreen title="Result detail" workspacePath="/app/lab/result-review" permission="lab.read">
      {({ accessToken, organizationId }) => (
        <DetailPanel itemId={itemId} accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function DetailPanel({
  itemId,
  accessToken,
  organizationId,
}: {
  itemId: string;
  accessToken: string;
  organizationId: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const state = useSourcedData(
    () => fetchTechnicianResult({ token: accessToken, organizationId }, itemId),
    [accessToken, organizationId, itemId],
  );
  const item = state.data;

  async function onValidate() {
    setBusy(true);
    try {
      await validateResult({ token: accessToken, organizationId }, itemId, "Technician validated");
      router.push("/app/lab/result-review");
    } finally {
      setBusy(false);
    }
  }

  async function onReject() {
    setBusy(true);
    try {
      await rejectResult({ token: accessToken, organizationId }, itemId, "Invalid result");
      router.push("/app/lab/result-review");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="Result detail" description="Inspect flags and validate before doctor review." />
      <DataState loading={state.loading} error={state.error} empty={!item} emptyLabel="Result not found." onRetry={state.reload}>
        {item && (
          <Card className="space-y-3 p-4 text-sm">
            <p className="font-medium">{String(item.test_code ?? item.test_name)}</p>
            <p>Original: {String(item.original_value ?? "—")}</p>
            <p>Normalized: {String(item.normalized_value ?? "—")}</p>
            <p>Status: {String(item.result_status ?? "—")}</p>
            <div className="flex gap-2 pt-2">
              <Button size="sm" onClick={onValidate} disabled={busy}>
                Validate
              </Button>
              <Button size="sm" variant="outline" onClick={onReject} disabled={busy}>
                Reject
              </Button>
            </div>
          </Card>
        )}
      </DataState>
    </div>
  );
}
