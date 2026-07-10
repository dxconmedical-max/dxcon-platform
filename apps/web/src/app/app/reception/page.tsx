import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Reception" };

export default function ReceptionPage() {
  return (
    <AppShell title="Reception" workspacePath="/app/reception">
      <WorkspaceHome
        title="Reception workspace"
        subtitle="Patient check-in, orders, and queue management."
        statusCards={[
          { label: "Queue", value: "—" },
          { label: "Orders", value: "—" },
          { label: "Payments", value: "—" },
          { label: "Print jobs", value: "—" },
        ]}
        actions={[
          { label: "Patient queue", href: "/app/reception", description: "Today's queue.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
