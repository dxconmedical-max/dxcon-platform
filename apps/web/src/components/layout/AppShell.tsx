"use client";

import { Header, MobileNav } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { useRequireAuth } from "@/hooks/useAuth";

export function AppShell({
  title,
  children,
  workspacePath,
}: {
  title: string;
  children: React.ReactNode;
  workspacePath: string;
}) {
  const auth = useRequireAuth(workspacePath);

  if (!auth.isHydrated || auth.status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
      </div>
    );
  }

  if (!auth.isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header title={title} />
        <main className="flex-1 p-4 lg:p-6">{children}</main>
        <MobileNav />
      </div>
    </div>
  );
}
