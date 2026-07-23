"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/stores/authStore";

const HYDRATION_FALLBACK_MS = 3_000;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const finishHydration = () => {
      const state = useAuthStore.getState();
      if (state.isHydrated) return;

      // Bootstrap must never leave status stuck on "loading" without a token.
      if (!state.accessToken) {
        console.debug("[AuthProvider] hydrate → unauthenticated (no token)");
        useAuthStore.setState({ isHydrated: true, status: "unauthenticated" });
        return;
      }

      console.debug("[AuthProvider] hydrate (token present → restore later)");
      useAuthStore.setState({ isHydrated: true, status: "loading" });
    };

    finishHydration();

    // Persist rehydrate is async; hard-stop so the login page cannot stay locked.
    const timer = window.setTimeout(() => {
      const state = useAuthStore.getState();
      if (!state.isHydrated) {
        console.debug("[AuthProvider] hydrate timeout → unauthenticated");
        useAuthStore.setState({ isHydrated: true, status: "unauthenticated" });
        return;
      }
      if (state.status === "loading" && !state.accessToken) {
        console.debug("[AuthProvider] clear stale loading without token");
        useAuthStore.setState({ status: "unauthenticated" });
      }
    }, HYDRATION_FALLBACK_MS);

    return () => window.clearTimeout(timer);
  }, []);

  return <>{children}</>;
}
