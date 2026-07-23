"use client";

import Link from "next/link";

import { Header, MobileNav } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/Button";
import { useRequireAuth } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

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
  const restoreSession = useAuthStore((s) => s.restoreSession);
  const logout = useAuthStore((s) => s.logout);
  const clearTransientFlags = useAuthStore((s) => s.clearTransientFlags);

  if (!auth.isHydrated || auth.isInitializingSession) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
        <p className="text-sm text-slate-500">Loading workspace…</p>
      </div>
    );
  }

  if (auth.error && !auth.isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-semibold text-slate-900">
            Unable to load workspace
          </h1>
          <p className="mt-2 text-sm text-slate-600" role="alert">
            {auth.error}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              type="button"
              onClick={() => {
                clearTransientFlags();
                void restoreSession();
              }}
            >
              Retry
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                void logout().then(() => {
                  window.location.href = "/login";
                });
              }}
            >
              Sign out
            </Button>
            <Link href="/login" className="text-sm text-teal-700 self-center">
              Back to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!auth.isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Redirecting to sign in…</p>
      </div>
    );
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
