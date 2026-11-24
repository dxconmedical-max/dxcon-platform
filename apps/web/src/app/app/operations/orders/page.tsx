import { AppShell } from "@/components/layout/AppShell";
import { OperationsBoard } from "@/components/pilot/OperationsBoard";

export const metadata = { title: "Bảng đơn hàng" };

export default function OperationsOrdersPage() {
  return (
    <AppShell title="Bảng đơn hàng" workspacePath="/app/operations">
      <OperationsBoard />
    </AppShell>
  );
}
