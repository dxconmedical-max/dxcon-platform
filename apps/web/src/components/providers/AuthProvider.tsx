"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/stores/authStore";

const HYDRATION_FALLBACK_MS = 3_000;

/**
 * Ensures persist hydration always terminates and never leaves transient
 * loading flags stuck — especially on the public login page.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const unlockAnonymous = () => {
      useAuthStore.setState({
        isHydrated: true,
        isInitializingSession: false,
        isSubmittingLogin: false,
        isRefreshingSession: false,
        status: "unauthenticated",
        error: null,
      });
    };

    const finishIfNeeded = () => {
      const state = useAuthStore.getState();
      if (state.isHydrated) {
        // Force-clear submit flag if a previous tab crash left it somehow.
        if (state.isSubmittingLogin) {
          useAuthStore.setState({ isSubmittingLogin: false });
        }
        return;
      }
      if (!state.accessToken) {
        console.debug("[AuthProvider] hydrate → anonymous");
        unlockAnonymous();
        return;
      }
      console.debug("[AuthProvider] hydrate → session restore pending");
      useAuthStore.setState({
        isHydrated: true,
        isInitializingSession: true,
        isSubmittingLogin: false,
        isRefreshingSession: false,
        error: null,
      });
    };

    finishIfNeeded();

    const timer = window.setTimeout(() => {
      const state = useAuthStore.getState();
      if (!state.isHydrated) {
        console.debug("[AuthProvider] hydrate timeout → anonymous");
        unlockAnonymous();
        return;
      }
      // Login page never calls restoreSession; do not leave init spinning.
      if (state.isInitializingSession && !state.accessToken) {
        useAuthStore.setState({ isInitializingSession: false });
      }
      if (state.isSubmittingLogin) {
        console.debug("[AuthProvider] clear stale isSubmittingLogin");
        useAuthStore.setState({ isSubmittingLogin: false });
      }
    }, HYDRATION_FALLBACK_MS);

    return () => window.clearTimeout(timer);
  }, []);

  return <>{children}</>;
}
