import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Laboratory" };

export default function LabPage() {
  return (
    <AppShell title="Laboratory" workspacePath="/app/lab">
      <WorkspaceHome
        title="Laboratory workspace"
        subtitle="Worklists, QC, and result verification."
        statusCards={[
          { label: "Worklist", value: "—" },
          { label: "Pending verify", value: "—" },
          { label: "Instruments", value: "—" },
          { label: "TAT", value: "—" },
        ]}
        actions={[
          { label: "Sample worklist", href: "/app/lab", description: "Processing queue.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
