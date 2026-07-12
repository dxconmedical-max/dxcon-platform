"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { searchDoctorPatients } from "@/lib/api/resources";


export default function DoctorPatientsPage() {
  return (
    <PilotListPage
      title="Patients"
      workspacePath="/app/doctor"
      permission="portal.doctor.read"
      emptyLabel="No assigned patients found."
      searchPlaceholder="Search patients"
      columns={[
        { key: "code", label: "Code", render: (r) => String(r.patient_code ?? "—") },
        { key: "name", label: "Name", render: (r) => String(r.full_name ?? r.name ?? "—") },
        { key: "phone", label: "Phone", render: (r) => String(r.phone ?? "—") },
      ]}
      fetchPage={(token, orgId, query, page) => searchDoctorPatients(token, orgId, query, page)}
    />
  );
}
