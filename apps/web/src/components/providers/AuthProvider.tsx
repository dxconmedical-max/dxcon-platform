"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/stores/authStore";

const HYDRATION_FALLBACK_MS = 3_000;

/**
 * Sole owner of initial session restoration for the browser app.
 * AppShell / useRequireAuth must NOT call restoreSession on mount.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const isHydrated = useAuthStore((s) => s.isHydrated);
  const bootstrapPhase = useAuthStore((s) => s.bootstrapPhase);
  const restoreSession = useAuthStore((s) => s.restoreSession);

  // Finish persist hydration if onRehydrateStorage is slow / missing.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      const s = useAuthStore.getState();
      if (s.isHydrated) return;
      console.debug("[AuthProvider] hydrate timeout → complete anonymous");
      useAuthStore.setState({
        isHydrated: true,
        bootstrapPhase: "complete",
        isInitializingSession: false,
        isSubmittingLogin: false,
        isRefreshingSession: false,
        status: "unauthenticated",
      });
    }, HYDRATION_FALLBACK_MS);
    return () => window.clearTimeout(timer);
  }, []);

  // Single restore owner — must not depend on user/session fields.
  useEffect(() => {
    if (!isHydrated) return;
    if (bootstrapPhase !== "idle") return;
    console.debug("[AuthProvider] sole restoreSession owner starting");
    void restoreSession();
  }, [isHydrated, bootstrapPhase, restoreSession]);

  return <>{children}</>;
}
