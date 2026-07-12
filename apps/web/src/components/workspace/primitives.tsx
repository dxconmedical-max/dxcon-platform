"use client";

import type { ReactNode } from "react";
import { MapPin, Navigation, QrCode, ScanLine } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { DataSource } from "@/lib/api/adapter";

export function SampleDataBadge({ source }: { source: DataSource }) {
  if (source === "live") {
    return <Badge tone="success">Live data</Badge>;
  }
  return (
    <Badge className="bg-amber-100 text-amber-800">Sample data</Badge>
  );
}

export function SectionHeader({
  title,
  description,
  actions,
  source,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  source?: DataSource;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
          {source ? <SampleDataBadge source={source} /> : null}
        </div>
        {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
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
  loading: boolean;
  error: string | null;
  empty: boolean;
  emptyLabel: string;
  onRetry?: () => void;
  children: ReactNode;
}) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-12 animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        {onRetry ? (
          <Button size="sm" className="mt-3" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
      </div>
    );
  }
  if (empty) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        {emptyLabel}
      </div>
    );
  }
  return <>{children}</>;
}

export type SimpleColumn<T> = {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
  className?: string;
};

export function SimpleTable<T>({
  columns,
  rows,
  rowKey,
}: {
  columns: SimpleColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 font-medium">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={rowKey(row, index)} className="border-b border-slate-100 last:border-0">
              {columns.map((column) => (
                <td key={column.key} className={`px-4 py-3 text-slate-700 ${column.className ?? ""}`}>
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const upper = status.toUpperCase();
  const good = ["COMPLETED", "CONFIRMED", "PAID", "VERIFIED", "RELEASED", "SIGNED", "CHECKED_IN", "PASS", "DONE"];
  const warn = ["WAITING", "PENDING", "AWAITING_REVIEW", "AWAITING_VERIFICATION", "DUE", "EN_ROUTE", "IN_TESTING", "RECEIVED", "ASSIGNED"];
  const bad = ["FAILED", "CANCELLED", "REJECTED", "CRITICAL", "OVERDUE"];
  let cls = "bg-slate-100 text-slate-700";
  if (good.includes(upper)) cls = "bg-emerald-50 text-emerald-700";
  else if (warn.includes(upper)) cls = "bg-amber-100 text-amber-800";
  else if (bad.includes(upper)) cls = "bg-rose-100 text-rose-700";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

/** Placeholder for the barcode/QR scanner hardware integration. */
export function ScannerPlaceholder({
  label = "Barcode / QR scanner",
  onSimulate,
}: {
  label?: string;
  onSimulate?: () => void;
}) {
  return (
    <Card className="flex flex-col items-center justify-center gap-3 border-dashed py-8 text-center">
      <ScanLine className="h-8 w-8 text-teal-600" />
      <div>
        <p className="text-sm font-medium text-slate-800">{label}</p>
        <p className="mt-1 text-xs text-slate-500">
          Camera scanner integration is planned. Use manual entry meanwhile.
        </p>
      </div>
      {onSimulate ? (
        <Button size="sm" variant="outline" onClick={onSimulate}>
          Simulate scan
        </Button>
      ) : null}
    </Card>
  );
}

/** Placeholder for the collector map / live route integration. */
export function MapPlaceholder({
  stops,
  onNavigate,
}: {
  stops?: number;
  onNavigate?: () => void;
}) {
  return (
    <Card className="border-dashed">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-teal-600" />
          <div>
            <p className="text-sm font-medium text-slate-800">Route map</p>
            <p className="text-xs text-slate-500">
              {stops ? `${stops} stop(s) on today's route.` : "Live map integration planned."}
            </p>
          </div>
        </div>
        <Button size="sm" variant="outline" onClick={onNavigate}>
          <Navigation className="h-4 w-4" />
          Navigate
        </Button>
      </div>
      <div className="mt-4 flex h-40 items-center justify-center rounded-xl bg-gradient-to-br from-teal-50 to-slate-100 text-xs text-slate-400">
        Map preview placeholder
      </div>
    </Card>
  );
}

/** QR confirmation panel rendered from an encoded payload. */
export function QrPanel({
  payload,
  caption,
}: {
  payload: string;
  caption?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white p-6 text-center">
      <div className="flex h-40 w-40 items-center justify-center rounded-xl border border-slate-200 bg-slate-50">
        <QrCode className="h-24 w-24 text-slate-800" aria-hidden />
      </div>
      <p className="break-all font-mono text-xs text-slate-500">{payload}</p>
      {caption ? <p className="text-sm text-slate-600">{caption}</p> : null}
    </div>
  );
}
