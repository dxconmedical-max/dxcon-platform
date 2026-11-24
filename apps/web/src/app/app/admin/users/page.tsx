import { AppShell } from "@/components/layout/AppShell";
import { StaffManager } from "@/components/pilot/StaffManager";

export const metadata = { title: "Tài khoản nhân viên" };

export default function AdminUsersPage() {
  return (
    <AppShell title="Tài khoản nhân viên" workspacePath="/app/admin/users">
      <StaffManager />
    </AppShell>
  );
}
