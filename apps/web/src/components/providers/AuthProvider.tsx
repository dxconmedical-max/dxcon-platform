"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";

function routeNeedsSession(pathname: string): boolean {
  return (
    pathname.startsWith("/app") ||
    pathname.startsWith("/marketplace") ||
    pathname === "/select-organization"
  );
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const status = useAuthStore((state) => state.status);
  const setHydrated = useAuthStore((state) => state.setHydrated);
  const restoreSession = useAuthStore((state) => state.restoreSession);

  useEffect(() => {
    if (!isHydrated) {
      setHydrated(true);
    }
  }, [isHydrated, setHydrated]);

  useEffect(() => {
    if (!isHydrated || status !== "loading") return;

    const { accessToken } = useAuthStore.getState();
    if (routeNeedsSession(pathname) || accessToken) {
      void restoreSession();
      return;
    }

    useAuthStore.setState({ status: "unauthenticated" });
  }, [isHydrated, pathname, restoreSession, status]);

  return <>{children}</>;
}
