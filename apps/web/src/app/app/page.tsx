import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Trang làm việc" };

export default function AppWorkspacePage() {
  return (
    <AppShell title="Tổng quan trang làm việc" workspacePath="/app">
      <WorkspaceHome
        title="Chào mừng đến với DxCon"
        subtitle="Trung tâm làm việc của anh/chị, kết nối với hệ thống DxCon."
        statusCards={[
          { label: "API", value: "Connected", hint: "api.dxcon.com.vn" },
          { label: "Trang làm việc", value: "General" },
          { label: "Tổ chức", value: "Active" },
          { label: "Tính năng", value: "Resolved" },
        ]}
        actions={[
          { label: "Quản trị", href: "/app/admin", description: "Cài đặt nền tảng." },
          { label: "Phòng xét nghiệm", href: "/app/lab", description: "Vận hành phòng xét nghiệm." },
          { label: "Báo cáo", href: "/app/admin/reporting", description: "Báo cáo đơn hàng và doanh thu theo ngày." },
        ]}
      />
    </AppShell>
  );
}
