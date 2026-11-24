import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Đưa khách hàng mới vào hệ thống" };

export default function AdminOnboardingPage() {
  return (
    <AppShell title="Khách hàng mới" workspacePath="/app/admin/onboarding">
      <WorkspaceHome
        title="Hướng dẫn đưa khách hàng mới vào hệ thống"
        subtitle="Phòng xét nghiệm, phòng khám, bệnh viện, bác sĩ, đơn vị thu mẫu và doanh nghiệp."
        statusCards={[
          { label: "Quy trình", value: "10 bước" },
          { label: "API", value: "/pilot-readiness/onboarding" },
          { label: "Đối tác đăng ký", value: "Quản trị duyệt" },
          { label: "Kích hoạt", value: "Phía máy chủ" },
        ]}
        actions={[
          {
            label: "Bắt đầu đưa phòng xét nghiệm vào hệ thống",
            href: "/onboarding/register",
            description: "Phòng khám và phòng xét nghiệm tự đăng ký.",
          },
          {
            label: "Thiết lập tổ chức",
            href: "/app/admin/organizations",
            description: "Logo, giao diện, phòng ban và dịch vụ.",
          },
          {
            label: "Nhập dữ liệu gốc",
            href: "/app/admin",
            description: "Nhập CSV/Excel qua MDM (Flask admin).",
          },
        ]}
      />
    </AppShell>
  );
}
