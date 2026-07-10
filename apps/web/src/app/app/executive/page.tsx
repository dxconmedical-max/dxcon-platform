import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Executive" };

export default function ExecutivePage() {
  return (
    <AppShell title="Executive" workspacePath="/app/executive">
      <WorkspaceHome
        title="Executive workspace"
        subtitle="Operational KPIs and strategic dashboards."
        statusCards={[
          { label: "Revenue", value: "—" },
          { label: "Volume", value: "—" },
          { label: "TAT", value: "—" },
          { label: "Quality", value: "—" },
        ]}
        actions={[
          { label: "KPI dashboard", href: "/app/executive", description: "Executive metrics.", comingSoon: true },
        ]}
      />
    </AppShell>
  );
}
