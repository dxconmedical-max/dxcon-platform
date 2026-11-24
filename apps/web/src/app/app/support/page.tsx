import { AppShell } from "@/components/layout/AppShell";
import { PilotReadinessHub } from "@/components/pilot/PilotReadinessHub";
import { SupportTickets } from "@/components/pilot/SupportTickets";

export const metadata = { title: "Trung tâm hỗ trợ" };

export default function SupportPage() {
  return (
    <AppShell title="Hỗ trợ" workspacePath="/app/support">
      <SupportTickets />
      <PilotReadinessHub
        title="Trung tâm hỗ trợ"
        subtitle="Phiếu hỗ trợ, sự cố và yêu cầu của khách hàng."
        endpoint="/api/v1/operations-center/dashboard"
      />
    </AppShell>
  );
}
