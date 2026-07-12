"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchOrders } from "@/lib/api/resources";


export default function DoctorOrdersPage() {
  return (
    <PilotListPage
      title="Orders"
      workspacePath="/app/doctor"
      permission="portal.doctor.read"
      emptyLabel="No orders available for your workspace."
      columns={[
        { key: "code", label: "Order", render: (r) => String(r.order_code ?? r.id ?? "—") },
        { key: "patient", label: "Patient", render: (r) => String(r.patient_id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchOrders(token, orgId)}
    />
  );
}
