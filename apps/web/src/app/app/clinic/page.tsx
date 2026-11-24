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
          { label: "Gửi phiếu chỉ định", href: "/app/clinic/new-request", description: "Nhập họ tên, năm sinh, xét nghiệm, số ống mẫu." },
          { label: "Reception desk", href: "/app/clinic/reception", description: "Theo dõi đơn xét nghiệm của phòng khám." },
        ]}
      />
    </AppShell>
  );
}
