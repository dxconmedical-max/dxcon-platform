import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Workspace" };

export default function AppWorkspacePage() {
  return (
    <AppShell title="Workspace overview" workspacePath="/app">
      <WorkspaceHome
        title="Welcome to DxCon"
        subtitle="Your central hub connected to the production API."
        statusCards={[
          { label: "API", value: "Connected", hint: "api.dxcon.com.vn" },
          { label: "Workspace", value: "General" },
          { label: "Organization", value: "Active" },
          { label: "Features", value: "Resolved" },
        ]}
        actions={[
          { label: "Administration", href: "/app/admin", description: "Platform settings." },
          { label: "Laboratory", href: "/app/lab", description: "Lab operations." },
          { label: "Reporting", href: "/app", description: "Analytics.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
