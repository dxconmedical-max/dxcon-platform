"use client";

import { useState } from "react";

import { Header, MobileNav } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { useRequireAuth } from "@/hooks/useAuth";
import { workspaceByPath } from "@/lib/workspaces";

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
  const [mobileOpen, setMobileOpen] = useState(false);
  const definition = workspaceByPath(workspacePath);

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
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-slate-900/40"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 shadow-xl">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          title={title}
          workspaceLabel={definition?.title}
          onMenuClick={() => setMobileOpen(true)}
        />
        <main className="flex-1 p-4 lg:p-6">{children}</main>
        <MobileNav />
      </div>
    </div>
  );
}
