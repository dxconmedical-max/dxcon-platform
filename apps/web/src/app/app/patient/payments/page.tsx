import { AppShell } from "@/components/layout/AppShell";

export const metadata = { title: "Payments" };

export default function PatientPaymentsPage() {
  return (
    <AppShell title="Payments" workspacePath="/app/patient">
      <p className="text-slate-600">Payment history and receipts.</p>
    </AppShell>
  );
}
