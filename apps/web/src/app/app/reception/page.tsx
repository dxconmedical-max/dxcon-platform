import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Reception" };

export default function ReceptionPage() {
  return (
    <AppShell title="Reception" workspacePath="/app/reception">
      <WorkspaceHome
        title="Reception workspace"
        subtitle="Milestone 1: patient search/create and diagnostic order creation against the production API."
        statusCards={[
          { label: "Patients", value: "Live" },
          { label: "Catalog", value: "Live" },
          { label: "Orders", value: "Live" },
          { label: "Payment", value: "M2" },
        ]}
        actions={[
          {
            label: "Create order",
            href: "/app/reception/workflow",
            description: "Patient → tests → authoritative order totals.",
          },
          {
            label: "Patient search",
            href: "/app/reception/search",
            description: "Search by phone, code, national ID, or name.",
          },
          {
            label: "Register patient",
            href: "/app/reception/register",
            description: "Walk-in registration with duplicate detection.",
          },
        ]}
      />
    </AppShell>
  );
}
