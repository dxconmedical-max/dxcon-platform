import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Patient" };

export default function PatientPage() {
  return (
    <AppShell title="Patient portal" workspacePath="/app/patient">
      <WorkspaceHome
        title="Patient portal"
        subtitle="Results, appointments, and home collection."
        statusCards={[
          { label: "Results", value: "—" },
          { label: "Appointments", value: "—" },
          { label: "Home visits", value: "—" },
          { label: "Messages", value: "—" },
        ]}
        actions={[
          { label: "My results", href: "/app/patient", description: "Released reports.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
