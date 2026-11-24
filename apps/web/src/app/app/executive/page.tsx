import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Điều hành" };

export default function ExecutivePage() {
  return (
    <AppShell title="Điều hành" workspacePath="/app/executive">
      <WorkspaceHome
        title="Không gian điều hành"
        subtitle="Chỉ số vận hành và bảng điều khiển chiến lược."
        statusCards={[
          { label: "Doanh thu", value: "—" },
          { label: "Số lượng", value: "—" },
          { label: "TAT", value: "—" },
          { label: "Chất lượng", value: "—" },
        ]}
        actions={[
          { label: "Bảng KPI", href: "/app/executive/kpi", description: "Doanh thu, đơn hàng, TAT và xét nghiệm nhiều nhất." },
        ]}
      />
    </AppShell>
  );
}
