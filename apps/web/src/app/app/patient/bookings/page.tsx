import { AppShell } from "@/components/layout/AppShell";

export const metadata = { title: "My bookings" };

export default function PatientBookingsPage() {
  return (
    <AppShell title="My bookings" workspacePath="/app/patient">
      <p className="text-slate-600">Patient booking history from marketplace API.</p>
    </AppShell>
  );
}
