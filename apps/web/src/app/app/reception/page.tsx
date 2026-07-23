import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Reception" };

export default function ReceptionPage() {
  return (
    <AppShell title="Reception" workspacePath="/app/reception">
      <WorkspaceHome
        title="Reception workspace"
        subtitle="Production patient intake, catalog orders, payment, and document generation."
        statusCards={[
          { label: "Queue", value: "Live" },
          { label: "Orders", value: "Live" },
          { label: "Payments", value: "Live" },
          { label: "Documents", value: "Live" },
        ]}
        actions={[
          {
            label: "Create order",
            href: "/app/reception/workflow",
            description: "Patient → tests → payment → barcode / requisition / QR.",
          },
          {
            label: "Patient search",
            href: "/app/reception/search",
            description: "Search production patients by code, name, phone, or ID.",
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
