"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";
import { fetchLabTestingQueue } from "@/lib/api/resources";


export default function LabSamplesPage() {
  return (
    <PilotListPage
      title="Testing queue"
      workspacePath="/app/lab"
      permission="lab.read"
      emptyLabel="No samples in the testing queue."
      columns={[
        { key: "sample", label: "Sample", render: (r) => String(r.sample_id ?? r.barcode ?? r.id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
        { key: "priority", label: "Priority", render: (r) => String(r.priority ?? "—") },
      ]}
      fetchPage={(token, orgId) => fetchLabTestingQueue(token, orgId)}
    />
  );
}
