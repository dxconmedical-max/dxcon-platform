"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Header, MobileNav } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { AuthErrorBoundary } from "@/components/providers/AuthErrorBoundary";
import { Button } from "@/components/ui/Button";
import { useRequireAuth } from "@/hooks/useAuth";
import { logAuthBootstrap } from "@/lib/auth/bootstrapDebug";
import {
  isBootstrapPending,
  useAuthStore,
} from "@/stores/authStore";

/** Hard ceiling for the shell spinner — never spin forever. */
export const APP_SHELL_BOOTSTRAP_TIMEOUT_MS = 15_000;

function BootstrapDiagnostic({
  title,
  message,
  detail,
  onRetry,
  onSignOut,
}: {
  title: string;
  message: string;
  detail?: string;
  onRetry: () => void;
  onSignOut: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-2 text-sm text-slate-600" role="alert">
          {message}
        </p>
        {detail ? (
          <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-700">
            {detail}
          </pre>
        ) : null}
        <div className="mt-6 flex flex-wrap gap-3">
          <Button type="button" onClick={onRetry}>
            Retry
          </Button>
          <Button type="button" variant="outline" onClick={onSignOut}>
            Sign out
          </Button>
          <Link href="/login" className="self-center text-sm text-teal-700">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}

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
  const storeError = useAuthStore((s) => s.error);
  const storePhase = useAuthStore((s) => s.bootstrapPhase);
  const storeStatus = useAuthStore((s) => s.status);
  const storeHydrated = useAuthStore((s) => s.isHydrated);
  const storeHasToken = useAuthStore((s) => Boolean(s.accessToken));
  const storeHasCapabilities = useAuthStore((s) => Boolean(s.capabilities));
  const storeRole = useAuthStore((s) => s.role);
  const [bootstrapTimedOut, setBootstrapTimedOut] = useState(false);
  const mountMs = useRef(
    typeof performance !== "undefined" ? performance.now() : Date.now(),
  );

  // Wait through idle/restoring — never classify anonymous until terminal.
  const bootstrapping =
    !auth.isHydrated || isBootstrapPending(auth.bootstrapPhase);

  // CRITICAL RACE: after login, status can be "authenticated" while
  // bootstrapPhase is still the /login hydrate value "anonymous".
  const staleAnonymousWhileAuthenticated =
    auth.bootstrapPhase === "anonymous" && auth.isAuthenticated;

  useEffect(() => {
    if (!bootstrapping) {
      setBootstrapTimedOut(false);
      return;
    }
    const timer = window.setTimeout(() => {
      const s = useAuthStore.getState();
      const stillBootstrapping =
        !s.isHydrated || isBootstrapPending(s.bootstrapPhase);
      if (!stillBootstrapping) return;
      console.error("[AppShell] bootstrap timed out", {
        bootstrapPhase: s.bootstrapPhase,
        status: s.status,
        isHydrated: s.isHydrated,
        hasToken: Boolean(s.accessToken),
        hasCapabilities: Boolean(s.capabilities),
        elapsedMs: Math.round(
          (typeof performance !== "undefined" ? performance.now() : Date.now()) -
            mountMs.current,
        ),
      });
      useAuthStore.setState({
        bootstrapPhase: "failed",
        isInitializingSession: false,
        error:
          s.error ||
          "Workspace bootstrap timed out. Session restore did not finish.",
      });
      setBootstrapTimedOut(true);
    }, APP_SHELL_BOOTSTRAP_TIMEOUT_MS);
    return () => window.clearTimeout(timer);
  }, [bootstrapping]);

  useEffect(() => {
    logAuthBootstrap("AppShell", {
      status: auth.status,
      bootstrapPhase: auth.bootstrapPhase,
      pathname:
        typeof window !== "undefined" ? window.location.pathname : undefined,
      sessionAuthenticated: auth.isAuthenticated,
      hasToken: Boolean(auth.accessToken),
      hasCapabilities: Boolean(auth.capabilities),
      redirectReason: bootstrapping
        ? "waiting_bootstrap"
        : staleAnonymousWhileAuthenticated
          ? "heal_stale_anonymous_phase"
          : auth.bootstrapPhase === "anonymous" && !auth.isAuthenticated
            ? "terminal_anonymous_redirect_ui"
            : auth.bootstrapPhase === "authenticated" && auth.isAuthenticated
              ? "render_shell"
              : storePhase === "failed"
                ? "failed"
                : "pending_or_ambiguous",
    });
  }, [
    auth.status,
    auth.bootstrapPhase,
    auth.isAuthenticated,
    auth.accessToken,
    auth.capabilities,
    bootstrapping,
    staleAnonymousWhileAuthenticated,
    storePhase,
  ]);

  useEffect(() => {
    if (!staleAnonymousWhileAuthenticated) return;
    // Heal the one-render race — phase must match authenticated status.
    useAuthStore.setState({ bootstrapPhase: "authenticated" });
  }, [staleAnonymousWhileAuthenticated]);

  const retryBootstrap = () => {
    setBootstrapTimedOut(false);
    clearTransientFlags();
    useAuthStore.setState({
      bootstrapPhase: "idle",
      error: null,
      isInitializingSession: true,
    });
    void restoreSession();
  };

  const signOut = () => {
    void logout().then(() => {
      window.location.href = "/login";
    });
  };

  if (bootstrapping && !bootstrapTimedOut) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
        <p className="text-sm text-slate-500">Loading workspace…</p>
      </div>
    );
  }

  const diagnosticError =
    storeError ||
    auth.error ||
    (bootstrapTimedOut
      ? "Workspace bootstrap timed out. Session restore did not finish."
      : null);

  if (
    bootstrapTimedOut ||
    storePhase === "failed" ||
    auth.bootstrapPhase === "failed"
  ) {
    return (
      <BootstrapDiagnostic
        title="Unable to load workspace"
        message={
          diagnosticError ||
          "Session restoration failed. The admin shell could not finish bootstrapping."
        }
        detail={[
          `phase=${storePhase}`,
          `status=${storeStatus}`,
          `hydrated=${String(storeHydrated)}`,
          `token=${storeHasToken ? "yes" : "no"}`,
          `capabilities=${storeHasCapabilities ? "yes" : "no"}`,
          `role=${storeRole ?? "none"}`,
        ].join("\n")}
        onRetry={retryBootstrap}
        onSignOut={signOut}
      />
    );
  }

  // Redirect UI only for true anonymous — never when session is authenticated.
  if (auth.bootstrapPhase === "anonymous" && !auth.isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Redirecting to sign in…</p>
      </div>
    );
  }

  if (
    (!auth.isAuthenticated || auth.bootstrapPhase !== "authenticated") &&
    !staleAnonymousWhileAuthenticated
  ) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
        <p className="text-sm text-slate-500">Loading workspace…</p>
      </div>
    );
  }

  if (!auth.capabilities) {
    return (
      <BootstrapDiagnostic
        title="Permissions not loaded"
        message="Your session is authenticated, but workspace capabilities never arrived. Retry bootstrap or sign in again."
        detail={[
          `phase=${auth.bootstrapPhase}`,
          `status=${auth.status}`,
          `role=${auth.role ?? "none"}`,
          `workspacePath=${workspacePath}`,
        ].join("\n")}
        onRetry={retryBootstrap}
        onSignOut={signOut}
      />
    );
  }

  return (
    <AuthErrorBoundary fallbackTitle="Workspace failed to render">
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header title={title} />
          <main className="flex-1 p-4 lg:p-6">{children}</main>
          <MobileNav />
        </div>
      </div>
    </AuthErrorBoundary>
  );
}
