"use client";

import { useEffect } from "react";

import {
  isBootstrapPending,
  useAuthStore,
} from "@/stores/authStore";

const HYDRATION_FALLBACK_MS = 3_000;
/** If phase stays idle/restoring with no completion, force a failed terminal state. */
const RESTORE_WATCHDOG_MS = 14_000;

/**
 * Sole owner of initial session restoration for the browser app.
 * AppShell / useRequireAuth must NOT call restoreSession on mount.
 *
 * Bootstrap: idle → restoring → authenticated | anonymous | failed
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
      // Prefer kicking restore if tokens already landed without isHydrated.
      if (s.accessToken && s.user) {
        console.debug("[AuthProvider] hydrate timeout → idle restore");
        useAuthStore.setState({
          isHydrated: true,
          bootstrapPhase: "idle",
          isInitializingSession: true,
          isSubmittingLogin: false,
          isRefreshingSession: false,
          status: "unauthenticated",
        });
        return;
      }
      console.debug("[AuthProvider] hydrate timeout → terminal anonymous");
      useAuthStore.setState({
        isHydrated: true,
        bootstrapPhase: "anonymous",
        isInitializingSession: false,
        isSubmittingLogin: false,
        isRefreshingSession: false,
        status: "unauthenticated",
      });
    }, HYDRATION_FALLBACK_MS);
    return () => window.clearTimeout(timer);
  }, []);

  // Single restore owner — only when phase is idle (tokens pending restore).
  useEffect(() => {
    if (!isHydrated) return;
    if (bootstrapPhase !== "idle") return;
    console.debug("[AuthProvider] sole restoreSession owner starting");
    void restoreSession();
  }, [isHydrated, bootstrapPhase, restoreSession]);

  // Safety net if restore never settles (hung promise, missing owner, etc.).
  useEffect(() => {
    if (!isHydrated) return;
    if (!isBootstrapPending(bootstrapPhase)) return;
    const timer = window.setTimeout(() => {
      const s = useAuthStore.getState();
      if (!isBootstrapPending(s.bootstrapPhase)) return;
      console.error("[AuthProvider] restore watchdog fired", {
        bootstrapPhase: s.bootstrapPhase,
        status: s.status,
        hasToken: Boolean(s.accessToken),
      });
      useAuthStore.setState({
        bootstrapPhase: "failed",
        isInitializingSession: false,
        isRefreshingSession: false,
        error:
          s.error ||
          "Authentication bootstrap did not complete. Please retry or sign in again.",
        status: s.accessToken ? s.status : "unauthenticated",
      });
    }, RESTORE_WATCHDOG_MS);
    return () => window.clearTimeout(timer);
  }, [isHydrated, bootstrapPhase]);

  return <>{children}</>;
}
