"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchOrders } from "@/lib/api/resources";


export default function AdminOrdersPage() {
  return (
    <PilotListPage
      title="Orders"
      workspacePath="/app/admin"
      permission="users.read"
      emptyLabel="No orders found."
      columns={[
        { key: "code", label: "Order", render: (r) => String(r.order_code ?? r.id ?? "—") },
        { key: "patient", label: "Patient", render: (r) => String(r.patient_id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchOrders(token, orgId)}
    />
  );
}
