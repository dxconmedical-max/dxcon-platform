import { AppShell } from "@/components/layout/AppShell";
import { LiveMap } from "@/components/pilot/LiveMap";

export const metadata = { title: "Live map" };

export default function LiveMapPage() {
  return (
    <AppShell title="Live map" workspacePath="/app/operations/live-map">
      <LiveMap />
    </AppShell>
  );
}
