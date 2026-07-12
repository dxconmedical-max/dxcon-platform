"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchPatientReleasedReports } from "@/lib/api/resources";


export default function PatientResultsPage() {
  return (
    <PilotListPage
      title="Released results"
      workspacePath="/app/patient"
      permission="portal.patient.read"
      emptyLabel="No released reports available yet."
      columns={[
        { key: "code", label: "Report", render: (r) => String(r.report_code ?? r.id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "released") },
        { key: "date", label: "Released", render: (r) => String(r.released_at ?? r.created_at ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchPatientReleasedReports(token, orgId)}
    />
  );
}
