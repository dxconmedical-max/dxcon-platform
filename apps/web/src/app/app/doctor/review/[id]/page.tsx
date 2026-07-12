"use client";

import Link from "next/link";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchDoctorReport } from "@/lib/api/doctor";
import { useParams } from "next/navigation";

export default function DoctorReviewDetailPage() {
  const params = useParams();
  const orderRef = String(params.id ?? "");
  return (
    <WorkspaceScreen title="Review detail" workspacePath="/app/doctor/review" permission="portal.doctor.read">
      {({ accessToken, organizationId }) => (
        <DetailPanel orderRef={orderRef} accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function DetailPanel({
  orderRef,
  accessToken,
  organizationId,
}: {
  orderRef: string;
  accessToken: string;
  organizationId: string;
}) {
  const state = useSourcedData(
    () => fetchDoctorReport({ token: accessToken, organizationId }, orderRef),
    [accessToken, organizationId, orderRef],
  );

  return (
    <div className="space-y-4">
      <SectionHeader title="Clinical review" description="Approve and sign before explicit release." />
      <DataState loading={state.loading} error={state.error} empty={!state.data} emptyLabel="Review not found." onRetry={state.reload}>
        {state.data && (
          <div className="space-y-2 text-sm">
            <p>Report: {String(state.data.report_code ?? orderRef)}</p>
            <p>Status: {String(state.data.status ?? "—")}</p>
            <Link href={`/app/doctor/reports/${encodeURIComponent(orderRef)}`}>
              <Button size="sm">Open full report workspace</Button>
            </Link>
          </div>
        )}
      </DataState>
    </div>
  );
}
