import { AppShell } from "@/components/layout/AppShell";
import { OrganizationManager } from "@/components/pilot/OrganizationManager";
import { PilotReadinessHub } from "@/components/pilot/PilotReadinessHub";

export const metadata = { title: "Organizations" };

export default function AdminOrganizationsPage() {
  return (
    <AppShell title="Organizations" workspacePath="/app/admin/organizations">
      <OrganizationManager />
      <PilotReadinessHub
        title="Organization management"
        subtitle="Tenant organizations, setup wizard, and partner foundation."
        endpoint="/api/v1/pilot-readiness/health-dashboard"
      />
    </AppShell>
  );
}
