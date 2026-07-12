"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchPatients } from "@/lib/api/resources";


export default function AdminPatientsPage() {
  return (
    <PilotListPage
      title="Patients"
      workspacePath="/app/admin"
      permission="users.read"
      emptyLabel="No patients found."
      searchPlaceholder="Search patients"
      columns={[
        { key: "code", label: "Code", render: (r) => String(r.patient_code ?? r.id ?? "—") },
        { key: "name", label: "Name", render: (r) => String(r.full_name ?? "—") },
        { key: "phone", label: "Phone", render: (r) => String(r.phone ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchPatients(token, orgId)}
    />
  );
}
