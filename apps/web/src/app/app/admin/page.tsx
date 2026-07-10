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
          { label: "User management", href: "/app/admin", description: "Accounts and roles.", comingSoon: true },
          { label: "Permission matrix", href: "/app/admin", description: "RBAC configuration.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
