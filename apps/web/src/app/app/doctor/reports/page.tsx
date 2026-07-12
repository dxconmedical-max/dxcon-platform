"use client";

import Link from "next/link";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchDoctorReviewQueue, type DoctorReviewRow } from "@/lib/api/doctor";

function ReportsPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<DoctorReviewRow[]>(
    () => fetchDoctorReviewQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Reports & reviews"
        description="Results awaiting clinical review and sign-off."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No reports awaiting review."
        onRetry={state.reload}
      >
        <SimpleTable<DoctorReviewRow>
          rows={rows}
          rowKey={(row) => row.report_code}
          columns={[
            { key: "report", label: "Report", render: (r) => r.report_code },
            { key: "patient", label: "Patient", render: (r) => r.patient_name },
            { key: "code", label: "Code", render: (r) => r.patient_code ?? "—" },
            { key: "collected", label: "Collected", render: (r) => r.collected_at ?? "—" },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
            {
              key: "action",
              label: "",
              render: (r) => (
                <Link href={`/app/doctor/reports/${encodeURIComponent(r.report_code)}`}>
                  <Button size="sm" variant="outline">
                    View
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

export default function DoctorReportsPage() {
  return (
    <WorkspaceScreen title="Reports" workspacePath="/app/doctor" permission="portal.doctor.read">
      {(ctx) => <ReportsPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
