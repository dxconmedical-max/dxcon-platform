import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Administration" };

export default function AdminPage() {
  return (
    <AppShell title="Administration" workspacePath="/app/admin">
      <WorkspaceHome
        title="Admin workspace"
        subtitle="Manage users, roles, and platform configuration."
        statusCards={[
          { label: "Users", value: "—" },
          { label: "Tenants", value: "—" },
          { label: "Security", value: "Active" },
          { label: "Audit", value: "—" },
        ]}
        actions={[
          { label: "Organizations", href: "/app/admin/organizations", description: "Tenant onboarding and setup." },
          { label: "Customer onboarding", href: "/app/admin/onboarding", description: "Wizard for new customers." },
          { label: "Integrations", href: "/app/admin/integrations", description: "Connectors and webhooks." },
          { label: "Operations", href: "/app/operations", description: "Production health and ops dashboard." },
        ]}
      />
    </AppShell>
  );
}
