"use client";

import Link from "next/link";

import { Button } from "@/components/ui/Button";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
      <h1 className="text-2xl font-semibold text-slate-900">Something went wrong</h1>
      <p className="mt-2 max-w-md text-center text-sm text-slate-600">
        The application encountered an unexpected error. You can retry or return to your workspace.
      </p>
      {error.digest ? (
        <p className="mt-2 text-xs text-slate-400">Reference: {error.digest}</p>
      ) : null}
      <div className="mt-6 flex gap-3">
        <Button onClick={reset}>Retry</Button>
        <Link href="/app">
          <Button variant="outline">Return to dashboard</Button>
        </Link>
        <Link href="/logout">
          <Button variant="ghost">Sign out</Button>
        </Link>
      </div>
    </div>
  );
}
