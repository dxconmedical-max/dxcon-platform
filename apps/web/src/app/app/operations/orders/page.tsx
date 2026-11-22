import { AppShell } from "@/components/layout/AppShell";
import { OperationsBoard } from "@/components/pilot/OperationsBoard";

export const metadata = { title: "Orders board" };

export default function OperationsOrdersPage() {
  return (
    <AppShell title="Orders board" workspacePath="/app/operations">
      <OperationsBoard />
    </AppShell>
  );
}
