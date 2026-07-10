import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Doctor" };

export default function DoctorPage() {
  return (
    <AppShell title="Doctor workspace" workspacePath="/app/doctor">
      <WorkspaceHome
        title="Doctor workspace"
        subtitle="Review results and manage patient care."
        statusCards={[
          { label: "Pending reviews", value: "—" },
          { label: "Patients", value: "—" },
          { label: "Critical flags", value: "—" },
          { label: "Messages", value: "—" },
        ]}
        actions={[
          { label: "Result inbox", href: "/app/doctor", description: "Verified results.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
