"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

export function SectionHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function DataState({
  loading,
  error,
  empty,
  emptyLabel,
  onRetry,
  children,
}: {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyLabel?: string;
  onRetry?: () => void;
  children: React.ReactNode;
}) {
  if (loading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        <p>{error}</p>
        {onRetry ? (
          <Button className="mt-3" size="sm" variant="outline" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
      </div>
    );
  }
  if (empty) {
    return (
      <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        {emptyLabel ?? "Nothing to show."}
      </p>
    );
  }
  return <>{children}</>;
}

export function StatusPill({ status }: { status: string }) {
  const tone =
    status === "approved" || status === "medically_validated" || status === "acceptable"
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : status === "rejected" || status === "critical_high" || status === "critical_low"
        ? "bg-rose-50 text-rose-800 border-rose-200"
        : status === "pending_review" || status === "tech_validated" || status === "testing"
          ? "bg-sky-50 text-sky-800 border-sky-200"
          : "bg-slate-50 text-slate-700 border-slate-200";
  return (
    <span className={cn("inline-flex rounded-md border px-2 py-0.5 text-xs font-medium", tone)}>
      {status}
    </span>
  );
}
