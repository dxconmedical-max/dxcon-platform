import { AppShell } from "@/components/layout/AppShell";
import { OperationsCollections } from "@/components/pilot/OperationsCollections";

export const metadata = { title: "Lấy mẫu tại nhà" };

export default function OperationsCollectionsPage() {
  return (
    <AppShell title="Lấy mẫu tại nhà" workspacePath="/app/operations">
      <OperationsCollections />
    </AppShell>
  );
}
