import { AppShell } from "@/components/layout/AppShell";
import { PilotReadinessHub } from "@/components/pilot/PilotReadinessHub";

export const metadata = { title: "Support Center" };

export default function SupportPage() {
  return (
    <AppShell title="Support" workspacePath="/app/support">
      <PilotReadinessHub
        title="Support center"
        subtitle="Tickets, incidents, and customer requests. Create tickets via the operations center API."
        endpoint="/api/v1/operations-center/dashboard"
      />
    </AppShell>
  );
}
