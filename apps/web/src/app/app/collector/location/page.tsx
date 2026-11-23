import { AppShell } from "@/components/layout/AppShell";
import { ShareLocation } from "@/components/pilot/ShareLocation";

export const metadata = { title: "Chia sẻ vị trí" };

export default function CollectorLocationPage() {
  return (
    <AppShell title="Chia sẻ vị trí" workspacePath="/app/collector">
      <ShareLocation />
    </AppShell>
  );
}
