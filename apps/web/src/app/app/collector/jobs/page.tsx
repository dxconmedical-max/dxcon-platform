"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";


async function emptyJobs(): Promise<{
  items: Record<string, unknown>[];
  total: number;
  page: number;
  pageSize: number;
}> {
  return { items: [], total: 0, page: 1, pageSize: 25 };
}

export default function CollectorJobsPage() {
  return (
    <PilotListPage<Record<string, unknown>>
      title="Assigned jobs"
      workspacePath="/app/collector"
      permission="collections.read"
      emptyLabel="No assigned collection jobs. Collector profile context may be required."
      columns={[
        { key: "job", label: "Job", render: (r) => String(r.assignment_id ?? r.id ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
      ]}
      fetchPage={async () => emptyJobs()}
    />
  );
}
