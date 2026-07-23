import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Reception" };

export default function ReceptionPage() {
  return (
    <AppShell title="Reception" workspacePath="/app/reception">
      <WorkspaceHome
        title="Reception workspace"
        subtitle="Patient intake, orders, payment, barcodes/QR, and laboratory requisitions."
        statusCards={[
          { label: "Patients", value: "Live" },
          { label: "Orders", value: "Live" },
          { label: "Payment", value: "Live" },
          { label: "Documents", value: "Live" },
        ]}
        actions={[
          {
            label: "Create order & documents",
            href: "/app/reception/workflow",
            description: "Patient → tests → payment → barcode/QR → requisition.",
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
