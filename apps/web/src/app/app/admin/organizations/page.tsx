import { AppShell } from "@/components/layout/AppShell";
import { OrganizationManager } from "@/components/pilot/OrganizationManager";
import { PilotReadinessHub } from "@/components/pilot/PilotReadinessHub";

export const metadata = { title: "Tổ chức" };

export default function AdminOrganizationsPage() {
  return (
    <AppShell title="Tổ chức" workspacePath="/app/admin/organizations">
      <OrganizationManager />
      <PilotReadinessHub
        title="Quản lý tổ chức"
        subtitle="Các tổ chức khách hàng, hướng dẫn thiết lập và đối tác."
        endpoint="/api/v1/pilot-readiness/health-dashboard"
      />
    </AppShell>
  );
}
