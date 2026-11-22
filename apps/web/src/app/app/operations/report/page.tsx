import { AppShell } from "@/components/layout/AppShell";
import { OperationsReport } from "@/components/pilot/OperationsReport";

export const metadata = { title: "Báo cáo" };

export default function OperationsReportPage() {
  return (
    <AppShell title="Báo cáo doanh thu" workspacePath="/app/operations">
      <OperationsReport />
    </AppShell>
  );
}
