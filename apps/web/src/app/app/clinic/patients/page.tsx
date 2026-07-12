"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchClinicPatients } from "@/lib/api/resources";


export default function ClinicPatientsPage() {
  return (
    <PilotListPage
      title="Patients"
      workspacePath="/app/clinic"
      permission="data.view"
      emptyLabel="No clinic patients found. Clinic context may be required."
      columns={[
        { key: "code", label: "Code", render: (r) => String(r.patient_code ?? r.id ?? "—") },
        { key: "name", label: "Name", render: (r) => String(r.full_name ?? r.name ?? "—") },
        { key: "phone", label: "Phone", render: (r) => String(r.phone ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchClinicPatients(token, orgId)}
    />
  );
}
