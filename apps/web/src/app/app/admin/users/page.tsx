import { AppShell } from "@/components/layout/AppShell";
import { StaffManager } from "@/components/pilot/StaffManager";

export const metadata = { title: "Staff accounts" };

export default function AdminUsersPage() {
  return (
    <AppShell title="Staff accounts" workspacePath="/app/admin/users">
      <StaffManager />
    </AppShell>
  );
}
