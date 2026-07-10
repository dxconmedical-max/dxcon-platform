import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Clinic" };

export default function ClinicPage() {
  return (
    <AppShell title="Clinic" workspacePath="/app/clinic">
      <WorkspaceHome
        title="Clinic workspace"
        subtitle="Reception, orders, and billing for your clinic."
        statusCards={[
          { label: "Visits", value: "—" },
          { label: "Orders", value: "—" },
          { label: "Billing", value: "—" },
          { label: "Referrals", value: "—" },
        ]}
        actions={[
          { label: "Reception desk", href: "/app/clinic", description: "Check-in and orders.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
