"use client";

import Link from "next/link";

import { WorkspaceScreen } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { DataState, SectionHeader, SimpleTable, StatusPill } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchDoctorClinicalQueue } from "@/lib/api/clinical";

export default function DoctorReviewPage() {
  return (
    <WorkspaceScreen title="Clinical review" workspacePath="/app/doctor/review" permission="portal.doctor.read">
      {({ accessToken, organizationId }) => (
        <ReviewPanel accessToken={accessToken} organizationId={organizationId} />
      )}
    </WorkspaceScreen>
  );
}

function ReviewPanel({ accessToken, organizationId }: { accessToken: string; organizationId: string }) {
  const state = useSourcedData(
    () => fetchDoctorClinicalQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data?.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Doctor review queue"
        description="Technician-validated results awaiting clinical approval and sign-off."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No reports awaiting doctor review."
        onRetry={state.reload}
      >
        <SimpleTable
          rows={rows}
          rowKey={(r) => String(r.report_code ?? r.id)}
          columns={[
            { key: "code", label: "Report", render: (r) => String(r.report_code ?? "—") },
            { key: "patient", label: "Patient", render: (r) => String(r.patient_name ?? r.patient_id ?? "—") },
            { key: "status", label: "Status", render: (r) => <StatusPill status={String(r.report_status ?? r.status ?? "—")} /> },
            {
              key: "action",
              label: "",
              render: (r) => (
                <Link href={`/app/doctor/review/${encodeURIComponent(String(r.report_code ?? r.order_code))}`}>
                  <Button size="sm" variant="outline">
                    Review
                  </Button>
                </Link>
              ),
            },
          ]}
        />
      </DataState>
    </div>
  );
}
