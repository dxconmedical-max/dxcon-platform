import { AppShell } from "@/components/layout/AppShell";
import { PilotReadinessHub } from "@/components/pilot/PilotReadinessHub";

export const metadata = { title: "Operations" };

export default function OperationsPage() {
  return (
    <AppShell title="Operations" workspacePath="/app/operations">
      <PilotReadinessHub
        title="Operations dashboard"
        subtitle="Today's orders, incidents, collectors, and SLA signals from the operations center."
        endpoint="/api/v1/pilot-readiness/operations-dashboard"
      />
    </AppShell>
  );
}
