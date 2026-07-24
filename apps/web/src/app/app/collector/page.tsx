import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Collector" };

export default function CollectorPage() {
  return (
    <AppShell title="Collector" workspacePath="/app/collector">
      <WorkspaceHome
        title="Sample Collection workspace"
        subtitle="Queue, verify identifiers, collect specimens, and track transport to laboratory arrival."
        statusCards={[
          { label: "Queue", value: "Live" },
          { label: "Collect", value: "Live" },
          { label: "Transport", value: "Live" },
          { label: "Lab arrival", value: "Live" },
        ]}
        actions={[
          {
            label: "Collection queue",
            href: "/app/collector/queue",
            description: "Specimens awaiting collection — filter by location, date, status, collector.",
          },
          {
            label: "Collect & transport",
            href: "/app/collector/workflow",
            description: "Verify patient/order, scan barcode, collect, dispatch, arrive at lab.",
          },
        ]}
      />
    </AppShell>
  );
}
