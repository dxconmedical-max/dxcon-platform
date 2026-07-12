"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchClinicOrders } from "@/lib/api/resources";


export default function ClinicOrdersPage() {
  return (
    <PilotListPage
      title="Orders"
      workspacePath="/app/clinic"
      permission="data.view"
      emptyLabel="No clinic orders found. Clinic context may be required."
      columns={[
        { key: "code", label: "Order", render: (r) => String(r.order_code ?? r.id ?? "—") },
        { key: "patient", label: "Patient", render: (r) => String(r.patient_id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchClinicOrders(token, orgId)}
    />
  );
}
