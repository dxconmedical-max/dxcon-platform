import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Collector" };

export default function CollectorPage() {
  return (
    <AppShell title="Collector" workspacePath="/app/collector">
      <WorkspaceHome
        title="Collector workspace"
        subtitle="Routes, pickups, and sample handover."
        statusCards={[
          { label: "Route", value: "—" },
          { label: "Pickups", value: "—" },
          { label: "In transit", value: "—" },
          { label: "Completed", value: "—" },
        ]}
        actions={[
          { label: "Route planner", href: "/app/collector", description: "Today's route.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
