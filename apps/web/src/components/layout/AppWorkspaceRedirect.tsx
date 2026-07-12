"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";

export function AppWorkspaceRedirect() {
  const router = useRouter();
  const { isHydrated, isAuthenticated, workspacePath, status } = useAuth();

  useEffect(() => {
    if (!isHydrated) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (status === "organization_required") {
      router.replace("/select-organization");
      return;
    }
    router.replace(workspacePath || "/app/admin");
  }, [isHydrated, isAuthenticated, workspacePath, status, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
    </div>
  );
}
