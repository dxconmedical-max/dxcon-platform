import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Laboratory" };

export default function LabPage() {
  return (
    <AppShell title="Laboratory" workspacePath="/app/lab">
      <WorkspaceHome
        title="Laboratory workspace"
        subtitle="Specimen receipt, accession, processing, result entry, and validation."
        statusCards={[
          { label: "Receive", value: "Live" },
          { label: "Accession", value: "Live" },
          { label: "Results", value: "Live" },
          { label: "Validation", value: "Live" },
        ]}
        actions={[
          {
            label: "Lab worklist",
            href: "/app/lab/queue",
            description: "Incoming and in-process specimens.",
          },
          {
            label: "Lab workflow",
            href: "/app/lab/workflow",
            description: "Receive → accession → process → results → tech & medical validation.",
          },
        ]}
      />
    </AppShell>
  );
}
