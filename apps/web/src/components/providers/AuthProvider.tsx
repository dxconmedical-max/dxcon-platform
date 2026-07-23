"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/stores/authStore";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const state = useAuthStore.getState();
    if (state.isHydrated) return;

    // Bootstrap status defaults to "loading". On the public login page we never
    // call restoreSession, so unlock immediately when there is no session token.
    // (Persist rehydrate also does this; this covers the no-storage path.)
    if (!state.accessToken && state.status === "loading") {
      console.debug("[AuthProvider] hydrate → unauthenticated (no token)");
      useAuthStore.setState({ isHydrated: true, status: "unauthenticated" });
      return;
    }

    console.debug("[AuthProvider] hydrate");
    useAuthStore.setState({ isHydrated: true });
  }, []);

  return <>{children}</>;
}
