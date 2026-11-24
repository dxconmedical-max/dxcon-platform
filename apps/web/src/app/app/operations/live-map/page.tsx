import { AppShell } from "@/components/layout/AppShell";
import { LiveMap } from "@/components/pilot/LiveMap";

export const metadata = { title: "Bản đồ trực tiếp" };

export default function LiveMapPage() {
  return (
    <AppShell title="Bản đồ trực tiếp" workspacePath="/app/operations">
      <LiveMap />
    </AppShell>
  );
}
