"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchPatientHistory } from "@/lib/api/resources";


export default function PatientOrdersPage() {
  return (
    <PilotListPage
      title="My orders"
      workspacePath="/app/patient"
      permission="portal.patient.read"
      emptyLabel="No orders found for your patient account."
      columns={[
        { key: "ref", label: "Reference", render: (r) => String(r.order_code ?? r.id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
        { key: "date", label: "Date", render: (r) => String(r.created_at ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchPatientHistory(token, orgId)}
    />
  );
}
