import { AppShell } from "@/components/layout/AppShell";
import { ShareLocation } from "@/components/pilot/ShareLocation";

export const metadata = { title: "Share location" };

export default function CollectorLocationPage() {
  return (
    <AppShell title="Share location" workspacePath="/app/collector">
      <ShareLocation />
    </AppShell>
  );
}
