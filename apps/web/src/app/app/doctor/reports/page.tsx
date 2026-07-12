"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchDoctorPendingReviews } from "@/lib/api/resources";


export default function DoctorReportsPage() {
  return (
    <PilotListPage
      title="Reports"
      workspacePath="/app/doctor"
      permission="portal.doctor.read"
      emptyLabel="No pending reports in your review queue."
      columns={[
        { key: "code", label: "Report", render: (r) => String(r.report_code ?? r.id ?? "—") },
        { key: "patient", label: "Patient", render: (r) => String(r.patient_code ?? r.patient_id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.report_status ?? r.status ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchDoctorPendingReviews(token, orgId)}
    />
  );
}
