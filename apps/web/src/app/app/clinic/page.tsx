import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Clinic" };

export default function ClinicPage() {
  return (
    <AppShell title="Phòng khám" workspacePath="/app/clinic">
      <WorkspaceHome
        title="Không gian phòng khám"
        subtitle="Tiếp nhận, đơn hàng và thanh toán của phòng khám."
        statusCards={[
          { label: "Lượt khám", value: "—" },
          { label: "Đơn hàng", value: "—" },
          { label: "Thanh toán", value: "—" },
          { label: "Chuyển tuyến", value: "—" },
        ]}
        actions={[
          { label: "Gửi phiếu chỉ định", href: "/app/clinic/new-request", description: "Nhập họ tên, năm sinh, xét nghiệm, số ống mẫu." },
          { label: "Bàn tiếp nhận", href: "/app/clinic/reception", description: "Theo dõi đơn xét nghiệm của phòng khám." },
        ]}
      />
    </AppShell>
  );
}
