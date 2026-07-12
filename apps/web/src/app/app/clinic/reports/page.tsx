"use client";

import { PilotListPage } from "@/components/pilot/PilotListPage";


async function emptyReports(): Promise<{
  items: Record<string, unknown>[];
  total: number;
  page: number;
  pageSize: number;
}> {
  return { items: [], total: 0, page: 1, pageSize: 25 };
}

export default function ClinicReportsPage() {
  return (
    <PilotListPage<Record<string, unknown>>
      title="Reports"
      workspacePath="/app/clinic"
      permission="data.view"
      emptyLabel="Clinic report listing is not available yet for this pilot workspace."
      columns={[
        { key: "code", label: "Report", render: (r) => String(r.report_code ?? "—") },
        { key: "status", label: "Status", render: (r) => String(r.status ?? "—") },
      ]}
      fetchPage={async () => emptyReports()}
    />
  );
}
